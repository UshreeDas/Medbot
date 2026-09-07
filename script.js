let currentChat = null;

function updateAuthButtons(isLoggedIn) {
    const authButtons = document.querySelector(".auth-buttons");
    const sidebar = document.getElementById("sidebar");
    if (!authButtons) return;

    const registerBtn = authButtons.querySelectorAll("button")[0];
    const loginBtn = authButtons.querySelectorAll("button")[1];
    const logoutBtn = authButtons.querySelectorAll("button")[2];

    if (!registerBtn || !loginBtn || !logoutBtn) return;

    if (sidebar && sidebar.classList.contains("collapsed")) {
        registerBtn.style.display = "none";
        loginBtn.style.display = "none";
        logoutBtn.style.display = "none";
        authButtons.style.display = "none";
        return;
    }

    if (isLoggedIn) {
        registerBtn.style.display = "none";
        loginBtn.style.display = "none";
        logoutBtn.style.display = "block";
        authButtons.style.display = "grid";
    } else {
        registerBtn.style.display = "block";
        loginBtn.style.display = "block";
        logoutBtn.style.display = "none";
        authButtons.style.display = "grid";
    }
}

// ---------------- ON LOAD ----------------
window.onload = () => {
    document.getElementById("messages").innerHTML = "";
    document.getElementById("chatList").innerHTML = "";
    updateAuthButtons(false);
};
// ---------------- LOGIN ----------------
async function login() {
    let username = prompt("Enter username:");
    let password = prompt("Enter password:");

    let res = await fetch("http://127.0.0.1:5000/login", {
        method: "POST",
        credentials: "include",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username, password})
    });

    let data = await res.json();

    if (data.status === "success") {
        alert("Login successful");
        updateAuthButtons(true);
        await loadChats();

        if (!currentChat) {
            await newChat();
        }
    } else {
        alert("Login failed");
    }
}

// ---------------- REGISTER ----------------
async function registerUser() {
    let username = prompt("Enter username:");
    let password = prompt("Enter password:");

    let res = await fetch("http://127.0.0.1:5000/register", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username, password})
    });

    let data = await res.json();

    if (data.status === "registered") {
        alert("Registered successfully ");
        updateAuthButtons(true);
        await login(); 
    } else {
        alert("Registration failed ");
    }
}

// ---------------- LOAD CHATS ----------------

// NEW ONE 
async function loadChats() {

    let res = await fetch("http://127.0.0.1:5000/get_chats", {
        credentials: "include"
    });

    let chats = await res.json();

    let list = document.getElementById("chatList");
    list.innerHTML = "";

    chats.forEach(chat => {

        // MAIN CHAT ROW
        let row = document.createElement("div");
        row.className = "chat-row";

        // CHAT NAME
        let name = document.createElement("span");
        name.innerText = chat;
        name.className = "chat-name";

        // OPEN CHAT
        name.onclick = () => loadChat(chat);

        // ACTION BUTTONS
        let actions = document.createElement("div");
        actions.className = "chat-actions";

        // RENAME BUTTON
        let renameBtn = document.createElement("button");
        renameBtn.innerHTML = `<i class="fa-solid fa-pen"></i>`;

        renameBtn.onclick = async (e) => {
            e.stopPropagation();

            let newName = prompt("Enter new chat name:");

            if (!newName) return;

            await renameChat(chat, newName);
        };

        // DELETE BUTTON
        let deleteBtn = document.createElement("button");
        deleteBtn.innerHTML = `<i class="fa-solid fa-trash"></i>`;

        deleteBtn.onclick = async (e) => {
            e.stopPropagation();

            let ok = confirm("Delete this chat?");

            if (!ok) return;

            await deleteChat(chat);
        };

        // APPEND
        actions.appendChild(renameBtn);
        actions.appendChild(deleteBtn);

        row.appendChild(name);
        row.appendChild(actions);

        list.appendChild(row);
    });

    // LOAD FIRST CHAT
    if (chats.length > 0) {
        currentChat = chats[0];
        await loadChat(currentChat);
    }
}

// ---------------- NEW CHAT ----------------
async function newChat() {

    currentChat = "chat_" + Date.now();

    let res = await fetch("http://127.0.0.1:5000/new_chat", {
        method: "POST",
        credentials: "include",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({chat_id: currentChat})
    });

    let data = await res.json();

    if (data.status === "error") {
        alert("Please login first");
        return;
    }

    document.getElementById("messages").innerHTML = "";

    await loadChats();
}
// ---------------- RENAME CHAT ----------------
async function renameChat(oldId, newId) {

    let res = await fetch("http://127.0.0.1:5000/rename_chat", {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            old_id: oldId,
            new_id: newId
        })
    });

    let data = await res.json();

    if (data.status === "renamed") {
        currentChat = newId;
        await loadChats();
    }
}


// ---------------- DELETE CHAT ----------------
async function deleteChat(chatId) {

    let res = await fetch("http://127.0.0.1:5000/delete_chat", {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            chat_id: chatId
        })
    });

    let data = await res.json();

    if (data.status === "deleted") {

        document.getElementById("messages").innerHTML = "";

        currentChat = null;

        await loadChats();
    }
}
// ---------------- LOAD CHAT ----------------
async function loadChat(chatId) {
    currentChat = chatId;

    let res = await fetch(`http://127.0.0.1:5000/history/${chatId}`, {
        credentials: "include"
    });

    let messages = await res.json();

    let box = document.getElementById("messages");
    box.innerHTML = "";

    messages.forEach(m => addMessage(m[0], m[1]));

    scrollToBottom();
}

// ---------------- SEND MESSAGE ----------------
async function sendMessage() {

    if (!currentChat) {
        alert("Create chat first");
        return;
    }

    let input = document.getElementById("input");
    let msg = input.value.trim();

    if (!msg) return;

    addMessage("user", msg);

    input.value = "";

    let messages = document.getElementById("messages");

    // SHOW TYPING ANIMATION
    let typingDiv = document.createElement("div");
    typingDiv.className = "typing";
    typingDiv.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;

    messages.appendChild(typingDiv);

    scrollToBottom();

    try {

        let res = await fetch("http://127.0.0.1:5000/chat", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: msg,
                chat_id: currentChat
            })
        });

        // REMOVE TYPING ANIMATION
        typingDiv.remove();

        const reader = res.body.getReader();//-------------------------------------------
const decoder = new TextDecoder();

let botDiv = document.createElement("div");
botDiv.className = "bot";

messages.appendChild(botDiv);

let buffer = "";

while (true) {

    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, {
        stream: true
    });

    let events = buffer.split("\n\n");

    buffer = events.pop();

    for (const event of events) {

        if (!event.startsWith("data:"))
            continue;

        const jsonText = event.substring(5).trim();

        if (!jsonText)
            continue;

        try {

            const data = JSON.parse(jsonText);

            if (data.type === "token") {

                botDiv.innerText += data.text;

                scrollToBottom();
            }

            else if (data.type === "sources") {

                createSourcesButton(
                    botDiv,
                    data.sources
                );
            }

            else if (data.type === "error") {

                botDiv.innerText +=
                    "\nError: " + data.message;
            }

        } catch (err) {

            console.error(
                "SSE parse error:",
                err
            );

        }
    }
} //--------------------------- 
    } catch (err) {

        typingDiv.remove();

        console.log(err);

        addMessage("bot", "Error getting response");
    }
}
// ------------------------------------------------
function createSourcesButton(botDiv, sources) {

    if (!sources || sources.length === 0)
        return;

    const sourceContainer = document.createElement("div");
    sourceContainer.className = "source-container";

    const sourceButton = document.createElement("button");
    sourceButton.className = "source-button";

    sourceButton.innerHTML =
        `<i class="fa-solid fa-book"></i> Sources`;

    const sourceImages = document.createElement("div");
    sourceImages.className = "source-images";
    sourceImages.style.display = "none";

    sources.forEach(filename => {

        const img = document.createElement("img");

        
        img.src =
            `http://127.0.0.1:5000/source/${encodeURIComponent(filename)}`;

        img.className = "source-image";
        img.alt = "Source document";

        sourceImages.appendChild(img);
    });

    sourceButton.onclick = () => {

        if (sourceImages.style.display === "none") {
            sourceImages.style.display = "flex";
        } else {
            sourceImages.style.display = "none";
        }
    };

    sourceContainer.appendChild(sourceButton);
    sourceContainer.appendChild(sourceImages);

    botDiv.appendChild(sourceContainer);
}
//----------------------------

// ---------------- UI HELPERS ----------------
function addMessage(role, text) {
    let div = document.createElement("div");
    div.className = role;
    div.innerText = text;

    document.getElementById("messages").appendChild(div);
    scrollToBottom();
}

function scrollToBottom() {
    let box = document.getElementById("messages");
    box.scrollTop = box.scrollHeight;
}

// ENTER TO SEND
document.addEventListener("keydown", function(e) {
    if (e.key === "Enter") {
        sendMessage();
    }
});

// SIDEBAR TOGGLE
function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");

    if (window.innerWidth <= 768) {
        sidebar.classList.toggle("active");
    } else {
        sidebar.classList.toggle("collapsed");
    }
}

// logout function
async function logoutUser() {

    await fetch("http://127.0.0.1:5000/logout", {
        method: "POST",
        credentials: "include"
    });

    currentChat = null;

    document.getElementById("messages").innerHTML = "";
    document.getElementById("chatList").innerHTML = "";
    updateAuthButtons(false);

    alert("Logged out");
}


let recognition;
let finalTranscript = "";
let silenceTimer;

function startListening() {
    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert("Speech recognition not supported in this browser");
        return;
    }

    recognition = new SpeechRecognition();

    // Select language from dropdown
    const lang = document.getElementById("langSelect").value;
    console.log("Selected language:", lang);
    recognition.lang = lang;

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    finalTranscript = "";

    const micBtn = document.getElementById("micBtn");
    micBtn.classList.add("listening");

    recognition.onresult = (event) => {
        let interim = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;

            if (event.results[i].isFinal) {
                finalTranscript += transcript + " ";
            } else {
                interim += transcript;
            }
        }

        // Show live text while speaking
        document.getElementById("input").value =
            finalTranscript + interim;

        // Reset 10-second timer whenever speech is detected
        clearTimeout(silenceTimer);

        silenceTimer = setTimeout(() => {
            recognition.stop();
        }, 5000); // 5 seconds of silence

        console.log("Detected:", finalTranscript + interim);//////////////
    };

    recognition.onend = () => {
        micBtn.classList.remove("listening");

        const text = finalTranscript.trim();

        if (text) {
            document.getElementById("input").value = text;
            sendMessage();
        }
    };

    recognition.onerror = (event) => {
        console.error("Speech error:", event.error);
        micBtn.classList.remove("listening");
    };
    console.log("Language:", recognition.lang); ///////
    recognition.start();
}


