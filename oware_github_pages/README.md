# Oware AI

GitHub Pagesで動作する、Oware（Abapa系ルール）のブラウザ版です。

## 公開方法
1. GitHubで新しいPublicリポジトリを作成
2. `index.html` をリポジトリ直下にアップロード
3. Settings → Pages を開く
4. Build and deployment で `Deploy from a branch` を選択
5. Branch を `main`、Folder を `/ (root)` にして Save
6. 数分後に表示される GitHub Pages URL からプレイ

## 現在の機能
- 4 seeds per pit、12 pits
- sowing / capture / grand-slam prevention / feeding rule
- 25 seeds到達または合法手なしで終了
- Minimax + alpha-beta pruning CPU
- 探索深度の変更
- 人間 vs CPU

## ルールについて
Owareには地域差があります。この実装は一般的なAbapa系のルールを仮定しています。大会・家庭ルールに合わせる場合は、特にfeeding rule、grand slam、終局時の残り石の扱いを確認してください。

## 今後の拡張
Pythonで自己対戦学習した評価モデルを、JSON等で書き出してJavaScript側へ読み込む構成に拡張できます。
