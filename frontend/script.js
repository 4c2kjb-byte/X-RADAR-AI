const chat = document.getElementById("chat");
const form = document.getElementById("askForm");
const input = document.getElementById("question");
const sendButton = document.getElementById("sendButton");


// =========================
// ADD MESSAGE
// =========================

function addMessage(text, role) {

    const message = document.createElement("div");

    message.className = `message ${role}`;


    // AI avatar
    if (role === "ai") {

        const avatar = document.createElement("div");

        avatar.className = "avatar";

        avatar.textContent = "AI";

        message.appendChild(avatar);
    }


    // Bubble
    const bubble = document.createElement("div");

    bubble.className = "bubble";

    bubble.textContent = text;

    message.appendChild(bubble);


    chat.appendChild(message);


    // Scroll to newest message
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: "smooth"
    });
}


// =========================
// ASK AI
// =========================

async function ask(question) {

    if (!question.trim()) {
        return;
    }


    // Show user's message
    addMessage(question, "user");


    // Clear input
    input.value = "";

    input.style.height = "auto";


    // Disable button
    sendButton.disabled = true;

    sendButton.textContent = "...";


    try {

        const response = await fetch("/api/ask", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question: question
            })

        });


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const data = await response.json();


        addMessage(
            data.answer || "لم يصل رد من الذكاء الاصطناعي.",
            "ai"
        );


    } catch (error) {

        console.error(error);

        addMessage(
            "تعذر الاتصال بالسيرفر. تأكد أن X Radar يعمل.",
            "ai"
        );

    } finally {

        sendButton.disabled = false;

        sendButton.textContent = "إرسال";
    }
}


// =========================
// FORM SUBMIT
// =========================

form.addEventListener("submit", function(event) {

    event.preventDefault();

    const question = input.value.trim();

    if (question) {

        ask(question);
    }

});


// =========================
// QUICK QUESTIONS
// =========================

document
    .querySelectorAll(".suggestion")
    .forEach(button => {

        button.addEventListener("click", function() {

            const question =
                this.textContent.trim();

            ask(question);

        });

    });


// =========================
// ENTER TO SEND
// =========================

input.addEventListener("keydown", function(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        form.requestSubmit();
    }

});


// =========================
// AUTO RESIZE
// =========================

input.addEventListener("input", function() {

    this.style.height = "auto";

    this.style.height =
        `${Math.min(this.scrollHeight, 140)}px`;

});
