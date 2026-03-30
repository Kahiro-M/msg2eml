import os
import glob
import extract_msg
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


scriptDir = Path(__file__).resolve().parent
os.chdir(scriptDir)

print('====== MSG to EML Converter ======')
print('                           v.1.0.0')

if not extract_msg:
    print('Error: "extract_msg"ライブラリが見つかりません。')
    print('このスクリプトを実行する前に、以下のコマンドで必要なライブラリをインストールしてください。')
    print('pip install extract_msg')
    exit(1)

# 変換元のMSGファイルが格納されている"input_msg"フォルダを確認
if not os.path.exists("input_msg"):
    print('Error: "input_msg"フォルダが見つかりません。')
    print('変換元のMSGファイルが格納されている"input_msg"フォルダを指定してください。')
    inputDir = input('フォルダパス: ')
    IN_DIR = Path(inputDir)
else:
    IN_DIR = Path("input_msg")

OUT_DIR = Path("output_eml")
ATT_DIR = OUT_DIR / "attachments"

OUT_DIR.mkdir(parents=True, exist_ok=True)
ATT_DIR.mkdir(parents=True, exist_ok=True)

for msg_path in glob.glob(str(IN_DIR / "*.msg")):
    name = Path(msg_path).stem
    emlPath = OUT_DIR / f"{name}.eml"
    base_attach_dir = ATT_DIR / name
    base_attach_dir.mkdir(parents=True, exist_ok=True)

    msg = extract_msg.Message(msg_path)

    #  EML本体をMIMEで手動組み立て 
    mime = MIMEMultipart()
    mime["Subject"] = msg.subject or ""
    mime["From"]    = msg.sender or ""
    mime["To"]      = msg.to or ""
    mime["Date"]    = str(msg.date) if msg.date else ""

    # 本文（HTML優先、なければプレーンテキスト）
    body_html  = msg.htmlBody
    body_plain = msg.body

    if body_html:
        # bytes の場合はデコード
        if isinstance(body_html, bytes):
            body_html = body_html.decode("utf-8", errors="replace")
        mime.attach(MIMEText(body_html, "html", "utf-8"))
    elif body_plain:
        if isinstance(body_plain, bytes):
            body_plain = body_plain.decode("utf-8", errors="replace")
        mime.attach(MIMEText(body_plain, "plain", "utf-8"))

    #  添付ファイル 
    for attach in msg.attachments:
        if attach.data is None:
            continue
        attach_name = attach.longFilename or attach.shortFilename or "attachment"
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attach.data)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=attach_name)
        mime.attach(part)

    #  EMLファイル書き出し
    emlPath.write_bytes(mime.as_bytes())

    print(f"Converted: {msg_path} -> {emlPath}")