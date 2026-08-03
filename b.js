let currentChat = null;

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
        alert("Registered successfully ✅");

        await login(); // auto login
    } else {
        alert("Registration failed ❌");
    }
}

// ---------------- LOAD CHATS ----------------
async function loadChats() {
    let res = await fetch("http://127.0.0.1:5000/get_chats", {
        credentials: "include"
    });

    let chats = await res.json();

    let list = document.getElementById("chatList");
    list.innerHTML = "";

    chats.forEach(chat => {
        let div = document.createElement("div");
        div.innerText = chat;
        div.onclick = () => loadChat(chat);
        list.appendChild(div);
    });

    if (chats.length > 0) {
        currentChat = chats[0];
        await loadChat(currentChat);
    }
}

// ---------------- NEW CHAT ----------------
async function newChat() {
    currentChat = "chat_" + Date.now();

    await fetch("http://127.0.0.1:5000/new_chat", {
        method: "POST",
        credentials: "include",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({chat_id: currentChat})
    });

    document.getElementById("messages").innerHTML = "";
    await loadChats();
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
    if (!currentChat) return alert("Create chat first");

    let input = document.getElementById("input");
    let msg = input.value;

    if (!msg) return;

    addMessage("user", msg);
    input.value = "";

    let res = await fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        credentials: "include",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            message: msg,
            chat_id: currentChat
        })
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    let botDiv = document.createElement("div");
    botDiv.className = "bot";
    document.getElementById("messages").appendChild(botDiv);

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        botDiv.innerText += decoder.decode(value);
        scrollToBottom();
    }
}

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