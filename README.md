# msg2eml

Outlookの*.msgファイルをThunderbirdの*.emlファイルへの変換ツール

## 環境
 - extract-msg 0.55.0

## 使用方法
### 変換元が`input_msg`フォルダの場合
1. Outlookからmsgファイルを出力
2. msgファイルを`input_msg`フォルダに保管
3. 同階層で`msg2eml.py`もしくは`msg2eml.exe`を実行
4. `output_eml`にemlファイルが出力される

### 変換元が`input_msg`フォルダ以外の場合
1. Outlookからmsgファイルを出力
2. msgファイルを任意のフォルダに保管
3. 同階層で`msg2eml.py`もしくは`msg2eml.exe`を実行
4. フォルダパスを指定
5. 指定したフォルダと同階層の`output_eml`にemlファイルが出力される

