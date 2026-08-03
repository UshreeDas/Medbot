let currentChat = null;
// ---------------- ON LOAD ----------------
window.onload = () => {
    document.getElementById("messages").innerHTML = "";
    document.getElementById("chatList").innerHTML = "";
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
// async function loadChats() {
//     let res = await fetch("http://127.0.0.1:5000/get_chats", {
//         credentials: "include"
//     });

//     let chats = await res.json();

//     let list = document.getElementById("chatList");
//     list.innerHTML = "";

//     chats.forEach(chat => {
//         let div = document.createElement("div");
//         div.innerText = chat;
//         div.onclick = () => loadChat(chat);
//         list.appendChild(div);
//     });

//     if (chats.length > 0) {
//         currentChat = chats[0];
//         await loadChat(currentChat);
//     }
// }
// NEW ONE ✅
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

        const reader = res.body.getReader();
        const decoder = new TextDecoder();

        let botDiv = document.createElement("div");
        botDiv.className = "bot";

        messages.appendChild(botDiv);

        while (true) {

            const { done, value } = await reader.read();

            if (done) break;

            let chunk = decoder.decode(value);

            botDiv.innerText += chunk;

            scrollToBottom();
        }

    } catch (err) {

        typingDiv.remove();

        console.log(err);

        addMessage("bot", "Error getting response");
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

    // Select language from your small dropdown
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


// let recognition = null;

// function startListening(){

//     if(!('webkitSpeechRecognition' in window)){

//         alert("Speech Recognition not supported in this browser.");
//         return;
//     }

//     recognition = new webkitSpeechRecognition();

//     // recognition.lang = "en-IN";          // English India
//     recognition.lang =document.getElementById("langSelect").value;
//     recognition.interimResults = true;
//     recognition.continuous = false;

//     const mic=document.getElementById("micBtn");

//     mic.classList.add("listening");

//     recognition.onresult=function(event){

//         let transcript="";

//         for(let i=event.resultIndex;i<event.results.length;i++){

//             transcript+=event.results[i][0].transcript;
//         }

//         document.getElementById("input").value=transcript;
//     };

//     recognition.onend=function(){

//         mic.classList.remove("listening");
//          if(document.getElementById("input").value.trim()!=""){

//         sendMessage();
//     }
//     };

//     recognition.onerror=function(){

//         mic.classList.remove("listening");
//     };

//     recognition.start();

// }




// let recorder;
// let chunks=[];

// async function startListening(){

//     const stream=await navigator.mediaDevices.getUserMedia({
//         audio:true
//     });

//     recorder=new MediaRecorder(stream);

//     chunks=[];

//     recorder.ondataavailable=e=>{
//         chunks.push(e.data);
//     };

//     recorder.onstop=sendAudio;

//     recorder.start();

//     document.getElementById("micBtn").classList.add("listening");
// }
// function stopListening(){

//     recorder.stop();

//     document.getElementById("micBtn").classList.remove("listening");
// }
// async function sendAudio(){

//     let blob=new Blob(chunks,{
//         type:"audio/webm"
//     });

//     let formData=new FormData();

//     formData.append("audio",blob);

//     let res=await fetch(
//         "http://127.0.0.1:5000/speech",
//         {
//             method:"POST",
//             body:formData
//         }
//     );

//     let data=await res.json();

//     document.getElementById("input").value=data.text;
//     sendMessage();

// }
// let recording=false;

// document.getElementById("micBtn").onclick=function(){

//     if(!recording){

//         recording=true;

//         startListening();

//     }else{

//         recording=false;

//         stopListening();

//     }

// }