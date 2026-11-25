"""Response-language support.

The FAQ/KB content is English, so retrieval always runs on an English query
(see query_understanding); only user-facing text is produced in the chosen
language — LLM-generated answers via `language_instruction`, and the fixed
follow-up/escalation messages via the translations below.
"""

from typing import Literal

LanguageCode = Literal["en", "ar", "fr", "pt"]

DEFAULT_LANGUAGE: LanguageCode = "en"

LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "ar": "Arabic",
    "fr": "French",
    "pt": "Portuguese",
}


def normalize_language(code: str | None) -> str:
    return code if code in LANGUAGE_NAMES else DEFAULT_LANGUAGE


def language_instruction(code: str | None) -> str:
    """Appended to system prompts whose output is shown to the user."""
    name = LANGUAGE_NAMES[normalize_language(code)]
    return (
        f"\n\nIMPORTANT: Write your entire response in {name}, regardless of the "
        f"language of the user's message or of the context excerpts. Keep product "
        f"names, role names, and email addresses/phone numbers as they are."
    )


# Prefix of the low-confidence follow-up message. Every translation is also
# used to recognise earlier follow-up turns in chat_history (see
# followup._consecutive_unsuccessful_attempts), so the attempt counter keeps
# working if the user switches language mid-conversation.
FOLLOWUP_PREFIXES: dict[str, str] = {
    "en": (
        "I couldn't find a fully confident answer to that yet. Here are some "
        "related questions I can help with:"
    ),
    "ar": (
        "لم أتمكن بعد من العثور على إجابة مؤكدة تمامًا لذلك. إليك بعض الأسئلة "
        "ذات الصلة التي يمكنني المساعدة فيها:"
    ),
    "fr": (
        "Je n'ai pas encore trouvé de réponse entièrement fiable à cette question. "
        "Voici quelques questions connexes sur lesquelles je peux vous aider :"
    ),
    "pt": (
        "Ainda não encontrei uma resposta totalmente segura para isso. Aqui estão "
        "algumas perguntas relacionadas com as quais posso ajudar:"
    ),
}

_OUT_OF_SCOPE_MESSAGES: dict[str, str] = {
    "en": (
        "Thanks for your question! This one seems to be outside what I can help "
        "with right now — I focus on TEF platform topics, and I don't have "
        "reliable information on this. I'd really appreciate your feedback "
        "below, and I'm happy to help with anything else about TEF."
    ),
    "ar": (
        "شكرًا على سؤالك! يبدو أن هذا السؤال خارج نطاق ما يمكنني المساعدة فيه "
        "حاليًا — فأنا أركز على مواضيع منصة TEF ولا تتوفر لدي معلومات موثوقة "
        "حول هذا الموضوع. يسعدني الاطلاع على رأيك أدناه، وأنا جاهز للمساعدة "
        "في أي أمر آخر يخص TEF."
    ),
    "fr": (
        "Merci pour votre question ! Elle semble sortir du cadre de ce que je peux "
        "traiter pour le moment — je me concentre sur les sujets de la plateforme "
        "TEF et je ne dispose pas d'informations fiables à ce sujet. Je serais "
        "ravi de recevoir vos commentaires ci-dessous, et je reste disponible "
        "pour toute autre question sur TEF."
    ),
    "pt": (
        "Obrigado pela sua pergunta! Parece estar fora do que posso ajudar neste "
        "momento — eu me concentro em temas da plataforma TEF e não tenho "
        "informações confiáveis sobre isso. Adoraria receber o seu feedback "
        "abaixo, e terei prazer em ajudar com qualquer outra dúvida sobre a TEF."
    ),
}


def followup_prefix(code: str | None) -> str:
    return FOLLOWUP_PREFIXES[normalize_language(code)]


def out_of_scope_message(code: str | None) -> str:
    return _OUT_OF_SCOPE_MESSAGES[normalize_language(code)]
