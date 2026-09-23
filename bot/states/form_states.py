"""Finite State Machine (FSM) states for interactive bot workflows."""
from aiogram.fsm.state import State, StatesGroup


class InstructionsForm(StatesGroup):
    waiting_for_instructions = State()


class TranslateForm(StatesGroup):
    waiting_for_language = State()
    waiting_for_text = State()


class CodeConvertForm(StatesGroup):
    waiting_for_language = State()
    waiting_for_code = State()


class InteractivePromptForm(StatesGroup):
    waiting_for_chat_input = State()
    waiting_for_think_input = State()
    waiting_for_web_input = State()
    waiting_for_code_input = State()
    waiting_for_debug_input = State()
    waiting_for_explain_input = State()
    waiting_for_optimize_input = State()
    waiting_for_review_input = State()
    waiting_for_summarize_input = State()
    waiting_for_rewrite_input = State()
    waiting_for_image_input = State()
