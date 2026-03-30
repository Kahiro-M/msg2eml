import sys
import os
import glob
import extract_msg
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

if getattr(sys, 'frozen', False):
    # PyInstallerで実行中
    baseDir = Path(sys.executable).parent
else:
    # 通常のPythonスクリプト実行中
    baseDir = Path(__file__).resolve().parent

os.chdir(baseDir)

print('====== MSG to EML Converter ======')
print('                           v.1.0.0')

if not extract_msg:
    print('Error: "extract_msg"ライブラリが見つかりません。')
    print('このスクリプトを実行する前に、以下のコマンドで必要なライブラリをインストールしてください。')
    print('pip install extract_msg')
    exit(1)

# 変換元のMSGファイルが格納されている"input_msg"フォルダを確認
if not os.path.exists("input_msg"):
    print('"input_msg"フォルダが見つかりません。')
    print('変換元のMSGファイルが格納されている"input_msg"フォルダを指定してください。')
    inputDir = input('フォルダパス: ')
    TMP_IN_DIR = Path(inputDir.strip().strip("'\"")).resolve()
else:
    TMP_IN_DIR = Path("input_msg")

IN_DIR = TMP_IN_DIR.resolve()
OUT_DIR = Path("output_eml").resolve()
OUT_DIR.mkdir(parents=True, exist_ok=True)

print('------ 変換元/出力先 ------')
print(f"Input Directory: {IN_DIR}")
print(f"Output Directory: {OUT_DIR}")

print('------ 変換開始 ------')
for msg_path in glob.glob(str(IN_DIR / "*.msg")):
    name = Path(msg_path).stem
    emlPath = OUT_DIR / f"{name}.eml"

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

    print(f"  Converted:")
    print(f"    {msg_path}")
    print(f"      -> {emlPath}")

print('------ 変換完了 ------')