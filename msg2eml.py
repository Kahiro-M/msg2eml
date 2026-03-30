import sys
import os
import glob
import extract_msg
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import format_datetime

if getattr(sys, 'frozen', False):
    # PyInstallerで実行中
    baseDir = Path(sys.executable).parent
else:
    # 通常のPythonスクリプト実行中
    baseDir = Path(__file__).resolve().parent

os.chdir(baseDir)

print('====== MSG to EML Converter ======')
print('                           v.1.0.1')

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
    # 必須項目をセット（存在しない場合は空文字列）
    mime["Subject"] = msg.subject or ""
    mime["From"]    = msg.sender or ""
    mime["To"]      = msg.to or ""

    # CcとBccは存在する場合のみセット
    if msg.cc:
        mime["Cc"] = msg.cc or ""
    if msg.bcc:
        mime["Bcc"] = msg.bcc or ""

    # 送信日時
    if msg.date:
        if msg.date.tzinfo is None:
            from datetime import timezone, timedelta
            jst = timezone(timedelta(hours=9))
            aware_date = msg.date.replace(tzinfo=jst)
            mime["Date"] = format_datetime(aware_date)
        else:
            mime["Date"] = format_datetime(msg.date)
    else:
        mime["Date"] = ""

    # 受信日時
    if msg.receivedTime:
        if msg.receivedTime.tzinfo is None:
            from datetime import timezone, timedelta
            jst = timezone(timedelta(hours=9))
            aware_date = msg.receivedTime.replace(tzinfo=jst)
            mime["Received"] = format_datetime(aware_date)
        else:
            mime["Received"] = format_datetime(msg.receivedTime)
    else:
        mime["Received"] = ""

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