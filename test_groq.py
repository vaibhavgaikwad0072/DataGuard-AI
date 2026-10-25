
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


def main():
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Check that your .env file exists "
            "in the project root."
        )

    llm = ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0,
    )

    response = llm.invoke(
        "Reply with exactly: DataGuard AI connection successful"
    )

    print(response.content)


if __name__ == "__main__":
    main()

