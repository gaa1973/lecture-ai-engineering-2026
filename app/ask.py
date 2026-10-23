"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保ったまま続けて質問する（宿題・実装）

ツールを持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def print_usage(response: types.GenerateContentResponse) -> None:
    usage = getattr(response, "usage_metadata", None)
    if usage is not None:
        prompt_tokens = getattr(usage, "prompt_token_count", None)
        output_tokens = getattr(usage, "candidates_token_count", None)
        print(f"[token usage] 入力={prompt_tokens} / 出力={output_tokens}")


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)
    print_usage(response)
    return response.text


def chat() -> None:
    """会話履歴を保ったまま、続けて質問する。

    LLM は前のやりとりを覚えていない。毎回これまでの履歴を全部送り直すことで、
    会話が続いているように見せている（そのため入力トークンは回を追うごとに増える）。
    """
    client = genai.Client(api_key=get_api_key())
    history: list[types.Content] = []

    print("会話モード（何も入力せずに Enter、または exit で終了）\n")
    while True:
        try:
            question = input("[質問] ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question in ("", "exit"):
            break

        history.append(types.Content(role="user", parts=[types.Part(text=question)]))
        try:
            response = client.models.generate_content(model=MODEL, contents=history)
        except errors.APIError as e:
            history.pop()  # 答えが返らなかった質問は履歴に残さない
            print(api_error_message(e.code, e.message) + "\n")
            continue

        answer = response.text or ""
        history.append(types.Content(role="model", parts=[types.Part(text=answer)]))
        print_usage(response)
        print(answer + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--chat", action="store_true", help="会話履歴を保ったまま続けて質問する")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    if args.chat:
        chat()
        return

    print(f"[質問] {args.question}\n")
    try:
        print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
