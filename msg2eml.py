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
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# サロゲート文字を含む可能性がある文字列を安全なUTF-8文字列に変換する
def sanitizeStr(value: str | None) -> str:
    if not value:
        return ""
    # surrogateescape でエンコードし、不正文字を '?' に置換して戻す
    return value.encode("utf-8", errors="replace").decode("utf-8", errors="replace")

# MSGファイルをEMLに変換する関数
def convertMsgToEml(msgPath):
    name = Path(msgPath).stem
    emlPath = OUT_DIR / f"{name}.eml"

    msg = extract_msg.Message(msgPath)

    #  EML本体をMIMEで手動組み立て 
    mime = MIMEMultipart()
    # 必須項目をセット（存在しない場合は空文字列）
    mime["Subject"] = sanitizeStr(msg.subject) or ""
    mime["From"]    = sanitizeStr(msg.sender) or ""
    mime["To"]      = sanitizeStr(msg.to) or ""

    # CcとBccは存在する場合のみセット
    if sanitizeStr(msg.cc):
        mime["Cc"] = sanitizeStr(msg.cc) or ""
    if sanitizeStr(msg.bcc):
        mime["Bcc"] = sanitizeStr(msg.bcc) or ""

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
        # attach.data が bytes でない場合はスキップまたは変換
        atchData = attach.data
        if not isinstance(atchData, bytes):
            try:
                atchData = bytes(atchData)
            except Exception:
                continue  # 変換不能な場合はこの添付をスキップ

        attach_name = attach.name or attach.longFilename or attach.shortFilename or attach.data.subject or attach.displayName or "attachment"
        part = MIMEBase("application", "octet-stream")
        part.set_payload(atchData)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=attach_name)
        mime.attach(part)

    #  EMLファイル書き出し
    emlPath.write_bytes(mime.as_bytes())
    return msgPath, emlPath



msgPaths = glob.glob(str(IN_DIR / "*.msg"))

print('------ 変換開始 ------')
with ThreadPoolExecutor() as executor:
    futures = {executor.submit(convertMsgToEml, p): p for p in msgPaths}
    for future in as_completed(futures):
        try:
            msgPath, emlPath = future.result()
            print(f" Converted:")
            print(f"  {msgPath}")
            print(f"  -> {emlPath}")
        except Exception as e:
            print(f" Error: {futures[future]} -> {e}")
print('------ 変換完了 ------')