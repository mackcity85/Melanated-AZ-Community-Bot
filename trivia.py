import random

from telegram import Update
from telegram.ext import ContextTypes



# ==========================================================
# TRIVIA QUESTION BANK
# ==========================================================

TRIVIA = [

    {
        "question": "What planet is known as the Red Planet?",
        "answer": "Mars"
    },

    {
        "question": "How many continents are there?",
        "answer": "7"
    },

    {
        "question": "What year did the first iPhone release?",
        "answer": "2007"
    },

    {
        "question": "What is the largest ocean on Earth?",
        "answer": "Pacific Ocean"
    },

    {
        "question": "Who painted the Mona Lisa?",
        "answer": "Leonardo da Vinci"
    },

    {
        "question": "What is the capital of Arizona?",
        "answer": "Phoenix"
    },

    {
        "question": "How many players are on a football team on the field?",
        "answer": "11"
    },

    {
        "question": "What element does the symbol Au represent?",
        "answer": "Gold"
    },

    {
        "question": "What is the fastest land animal?",
        "answer": "Cheetah"
    },

    {
        "question": "How many days are in a leap year?",
        "answer": "366"
    }

]



# ==========================================================
# TRIVIA COMMAND
# ==========================================================

async def trivia(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    question = random.choice(
        TRIVIA
    )


    context.chat_data["trivia_answer"] = (
        question["answer"].lower()
    )


    await update.message.reply_text(
        "🧠 MELANATED AZ TRIVIA\n\n"
        f"❓ {question['question']}\n\n"
        "Reply with your answer!"
    )



# ==========================================================
# TRIVIA ANSWER CHECK
# ==========================================================

async def trivia_answer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if "trivia_answer" not in context.chat_data:

        return


    user_answer = (
        update.message.text.lower()
    )


    correct_answer = (
        context.chat_data["trivia_answer"]
    )


    if user_answer == correct_answer:


        await update.message.reply_text(
            f"🎉 Correct {update.effective_user.first_name}!\n"
            f"The answer was {correct_answer.title()}."
        )


        del context.chat_data["trivia_answer"]
