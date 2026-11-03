# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：「AIE2026の講座の宿題にある『3レベル』とは何ですか？」に対して、第1回の `app.ask` は「AIE2026」が何かを知らないまま、一般的な3段階（基礎＝穴埋め、応用＝自力実装、発展＝ゼロから構築）で答えた。第3回の `app.agent` は用語集を検索してから答え、「基礎（講義内容の確認）・実装（自分でコードを書く）・発展（調査や試行）。どれか1つで完了、原則採点なし」と、`data/glossary.json` の `homework-levels` の定義どおりだった。最後に関係する回（第1回）も付いた。（モデル: gemini-3.5-flash-lite）
- `--trace` で見えたツール呼び出し（ツール名と引数）：「LoRA とQLoRAの違いは？」で `search_glossary({'query': 'LoRA'})` と `search_glossary({'query': 'QLoRA'})` の2回。用語を1つずつ検索していた。
- 1つの質問での LLM 呼び出し回数（`requests`）：`requests=2`（`tool_calls=2`）。1回目で検索を依頼し、2回目で結果を読んで答えた。道具を使う周が増えるほど、増える。「第3回の要点を読んで、そこに出てくる用語を1つ選び、用語集で調べて説明して」では、`get_lecture_summary({'lecture': 3})` → `search_glossary({'query': 'Pydantic AI'})` の順に呼ばれ、`requests=3`（`tool_calls=2`）だった。2つ目の検索語は1つ目の結果を読まないと決められないので、道具を使う周が2回になった。
- 追加したツールと、docstring に書いた説明：`make_quiz(lecture: int)`。docstring は「指定した回の用語から1つを選び、確認問題と答えを返す。『第2回の確認問題を出して』のように、復習用の問題を求められたときに使う。lecture には回の番号（1始まりの整数）を入れる。」`--list-tools` に出ること、`--trace "第2回の内容から確認問題を1問出して"` で `make_quiz({'lecture': 2})` が呼ばれること、`uv run pytest -q` が通ること（11 passed）を確認した。

## 宿題

- 取り組んだレベル：実装
- やったこと：`app/tools.py` に `save_learning_log(title, content)` を作った。`learning_log/日付_題名.md` に Markdown で保存し、同じ名前があれば `_2` を付けて上書きしない。`app/agent.py` では `requires_approval=True` を付けて登録し、`output_type=[str, DeferredToolRequests]` にした。止まったあとは `ask_approvals()` で保存してよいか `[y/N]` を聞き、その答え（`DeferredToolResults`）と `message_history=result.all_messages()` を渡して2回目の `run_sync` を実行する。`INSTRUCTIONS` に「記録を頼まれたら save_learning_log を使う」を1行足した。
- 結果：「第3回で学んだことを学習の記録として保存して」を `--trace` 付きで2回実行した。
  - `n` のとき：`[承認待ち] save_learning_log(...)` で止まり、`[tool return] save_learning_log -> The tool call was denied.` になった。ファイルはできなかった。
  - `y` のとき：`[tool return] save_learning_log -> 保存しました: learning_log/2026-11-03_第3回_学習記録_AIエージェント.md` になり、ファイルができた。
  - どちらも、保存の前に `get_lecture_summary({'lecture': 3})` が呼ばれていた。止まらなかったのは、`requires_approval=True` を付けていない道具（`search_glossary`・`get_lecture_summary`）。
  - 承認で止まる質問は、`requests` が承認の前と続きに分かれる（画面の `requests=1` は続きの分だけ。承認の前の2回と合わせて3回）。
- 気づき・疑問：
  - エージェントと、回答の正しさに相関性はない。
  - ループの仕組みについても、コードの確認だけではわからなかった。
  - ループを止めるにも、今回はコードの中に固定となっており、実際にはLLMが自分で判断する仕組みになっていると予想した。その後ライブラリのコードを読むと、止めるかどうかを実行時に決める場合も、決めるのはLLMではなく、道具の中で `ApprovalRequired` を投げるコードだと分かった（ライブラリの記述から読み取っただけで、今回は使っておらず、動かして確かめてはいない）。LLMが決めるのは、どの道具をいつ呼ぶかまで。
