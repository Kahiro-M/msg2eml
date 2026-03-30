import os
import glob
import extract_msg
from pathlib import Path


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
msgDir = Path(scriptDir)

for msg_path in glob.glob(str(IN_DIR / "*.msg")):
    name = Path(msg_path).stem
    emlPath = OUT_DIR / f"{name}.eml"
    base_attach_dir = ATT_DIR / name
    base_attach_dir.mkdir(parents=True, exist_ok=True)

    msg = extract_msg.Message(msg_path)

    # EML本体を書き出し
    # os.chdir(OUT_DIR)
    emlPath.write_bytes(msg.exportBytes())

    # 添付を書き出し
    # ※添付の仕様（埋め込み/通常添付等）によっては、出力された形式が異なる場合があります
    for i, attach in enumerate(msg.attachments):
        # 添付名が取れない場合があるのでフォールバック
        attach_name = attach.longFilename or attach.shortFilename or f"attachment_{i+1}"

        out_file = base_attach_dir / attach_name
        # 文字コード等で失敗する場合は try/except が必要になることがあります
        with open(out_file, "wb") as f:
            f.write(attach.data)

    # os.chdir(msgDir)

    print(f"Converted: {msg_path} -> {emlPath}")