"""Unit and integration test verification for AVEN AI."""
import asyncio
from database.db import db_manager
from database.repository import repo
from utils.formatting import markdown_to_telegram_html
from utils.splitter import split_message, prepare_response_delivery
from providers.auto import AutoProvider
from providers.registry import registry


async def run_tests():
    print("1. Testing SQLite Database...")
    await db_manager.initialize()
    test_uid = 888888
    await repo.reset_user_settings(test_uid)
    user = await repo.get_or_create_user(test_uid, "aven_tester", "Tester")
    assert user.user_id == test_uid
    assert user.model == "aven_auto"
    print("   [+] User creation and default settings verified.")

    await repo.update_user_model(test_uid, "aven_flash")
    user = await repo.get_or_create_user(test_uid)
    assert user.model == "aven_flash"
    print("   [+] User model switching verified.")

    await repo.update_user_temperature(test_uid, 1.0)
    await repo.update_user_theme(test_uid, "cyber")
    await repo.update_user_instructions(test_uid, "Always respond in bullet points.")
    user = await repo.get_or_create_user(test_uid)
    assert user.temperature == 1.0
    assert user.theme == "cyber"
    assert user.custom_instructions == "Always respond in bullet points."
    print("   [+] User preferences and custom instructions verified.")

    await repo.clear_history(test_uid)
    await repo.add_message(test_uid, "user", "Explain recursion", "aven_flash")
    await repo.add_message(test_uid, "assistant", "Recursion is when a function calls itself.", "aven_flash")
    msgs = await repo.get_recent_messages(test_uid)
    assert len(msgs) == 2
    assert msgs[0].role == "user"
    assert msgs[1].role == "assistant"
    print("   [+] Chat history sliding window verified.")

    stats = await repo.get_system_stats(test_uid)
    assert stats["total_users"] >= 1
    assert stats["total_messages"] >= 2
    assert stats["user_messages"] == 2
    print("   [+] System analytics and metrics verified.")

    print("\n2. Testing Formatter (Markdown to Safe Telegram HTML)...")
    sample_md = (
        "# Overview\n"
        "Here is **bold text** and *italic text* and `inline_code`.\n"
        "> Important blockquote statement.\n"
        "```python\n"
        "def hello_aven():\n"
        "    print('Hello World')\n"
        "```\n"
        "[Documentation](https://aven.ai)"
    )
    html_res = markdown_to_telegram_html(sample_md)
    assert "<b>Overview</b>" in html_res
    assert "<b>bold text</b>" in html_res
    assert "<i>italic text</i>" in html_res
    assert "<code>inline_code</code>" in html_res
    assert "<blockquote>Important blockquote statement.</blockquote>" in html_res
    assert '<pre><code class="language-python">' in html_res
    assert '<a href="https://aven.ai">Documentation</a>' in html_res
    print("   [+] Telegram HTML parsing and tag formatting verified.")

    print("\n3. Testing Message Splitter...")
    long_code = "```python\n" + ("print('AVEN line')\n" * 150) + "```"
    chunks = split_message(long_code, max_length=500)
    assert len(chunks) > 1
    for idx, c in enumerate(chunks):
        assert c.count("```") % 2 == 0, f"Chunk {idx} has unmatched code fence"
    print("   [+] Code block boundary preservation across splits verified.")

    print("\n4. Testing Auto Router Intent Classification...")
    auto_p = AutoProvider(registry=registry)
    assert auto_p.classify_intent("write a python script to parse json") == "code"
    assert auto_p.classify_intent("what is the stock price today 2026") == "web"
    assert auto_p.classify_intent("prove that square root of 2 is irrational") == "reasoning"
    assert auto_p.classify_intent("hello, what is your name?") == "fast"
    print("   [+] Intent classification (code, web, reasoning, fast) verified.")

    print("\n5. Testing Provider Registry...")
    available_models = registry.get_available_models()
    print(f"   [+] Available model count without keys configured: {len(available_models)}")
    # Aven Auto and Web are structurally available, concrete models require their respective keys
    assert registry.get_provider_by_model_id("aven_flash") is not None
    assert registry.get_provider_by_model_id("aven_swift") is not None
    assert registry.get_provider_by_model_id("aven_pro") is not None
    assert registry.get_provider_by_model_id("aven_auto") is not None
    print("   [+] All provider endpoints mapped correctly.")

    print("\n==========================================")
    print("[SUCCESS] ALL 5 TEST SUITES PASSED FLAWLESSLY!")
    print("==========================================")


if __name__ == "__main__":
    asyncio.run(run_tests())
