from typing import Any, Dict, List

from openai import AsyncOpenAI

from .config import OPENAI_API_KEY, OPENAI_MODEL


# =========================
# OPENAI CLIENT
# =========================

client = (
    AsyncOpenAI(api_key=OPENAI_API_KEY)
    if OPENAI_API_KEY
    else None
)


# =========================
# SYSTEM PROMPT
# =========================

SYSTEM_PROMPT = """
أنت X Radar AI.

مهمتك تحليل المنشورات التي ظهرت في For You
للمستخدم على منصة X.

أنت لا تتصفح X بنفسك.
أنت تعتمد فقط على المنشورات التي يتم إرسالها لك.

قواعد مهمة:

1. لا تخترع منشورات أو معلومات غير موجودة في البيانات.
2. لا تدّعي أنك رأيت شيئًا لم يتم إرساله لك.
3. إذا كانت البيانات غير كافية، قل ذلك بوضوح.
4. ركز على الأنماط والمواضيع والتكرار والإشارات المهمة.
5. عند طلب أفضل المنشورات، اخترها بناءً على
   مدى ارتباطها بالسؤال وقيمتها المعلوماتية.
6. عند طلب "وش أكثر شيء كان يدور؟"
   ابحث عن الموضوعات المتكررة والمشتركة.
7. عند طلب مقارنة، قارن فقط البيانات المتاحة.
8. عند طلب المنشورات الأصلية، اعرض النصوص الموجودة
   كما هي قدر الإمكان ولا تغير معناها.
9. لا تنسب رأيًا إلى صاحب منشور لم يقله.
10. لا تضف معلومات من خارج البيانات إلا إذا كان
    السؤال يحتاج تفسيرًا عامًا، وعندها وضح أنه تفسير.
11. أجب باللغة العربية بشكل طبيعي وواضح.
12. كن مختصرًا عندما يكون السؤال بسيطًا.
13. كن أكثر تفصيلًا عندما يحتاج السؤال إلى تحليل.

أسلوبك:
ذكي، هادئ، مباشر، تحليلي.

الفكرة الأساسية:
أنت لا تكتفي بتلخيص الـ For You،
بل تساعد المستخدم على فهم ما يحدث فيه.
"""


# =========================
# FORMAT POSTS
# =========================

def format_posts(
    posts: List[Dict[str, Any]]
) -> str:

    if not posts:
        return "لا توجد منشورات متاحة حاليًا."

    chunks = []

    for index, post in enumerate(posts, start=1):

        author = post.get(
            "author",
            ""
        )

        username = post.get(
            "username",
            ""
        )

        text = post.get(
            "text",
            ""
        )

        url = post.get(
            "url",
            ""
        )

        created_at = post.get(
            "created_at",
            ""
        )

        chunks.append(
            f"""
[منشور {index}]

الكاتب:
{author}

المستخدم:
@{username}

النص:
{text}

الرابط:
{url}

وقت المنشور:
{created_at}
"""
        )

    return "\n".join(chunks)


# =========================
# ASK AI
# =========================

async def ask_ai(
    question: str,
    posts: List[Dict[str, Any]]
) -> str:

    if not question.strip():

        return "اكتب سؤالك أولًا."


    if client is None:

        return (
            "لم يتم إعداد OPENAI_API_KEY بعد."
        )


    posts_text = format_posts(posts)


    user_prompt = f"""
السؤال من المستخدم:

{question}

المنشورات المتاحة من For You:

{posts_text}

حلل البيانات السابقة وأجب عن سؤال المستخدم.

لا تخترع معلومات غير موجودة في المنشورات.
"""


    try:

        response = await client.responses.create(

            model=OPENAI_MODEL,

            instructions=SYSTEM_PROMPT,

            input=user_prompt,

        )

        answer = response.output_text.strip()

        if not answer:

            return (
                "لم يتم الحصول على إجابة من نموذج الذكاء الاصطناعي."
            )

        return answer


    except Exception as error:

        print(
            "OpenAI error:",
            error
        )

        return (
            "حدث خطأ أثناء الاتصال بالذكاء الاصطناعي. "
            "تأكد من إعداد مفتاح OpenAI واسم النموذج."
        )
