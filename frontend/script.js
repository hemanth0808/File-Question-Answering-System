let currentFile = null;
let fileContent = null;
let isOpenAIEnabled = true; // Toggle between OpenAI and Hugging Face

document.addEventListener("DOMContentLoaded", () => {
  // DOM elements
  const dropArea = document.getElementById("dropArea");
  const fileInput = document.getElementById("fileInput");
  const fileInfo = document.getElementById("fileInfo");
  const questionInput = document.getElementById("questionInput");
  const askButton = document.getElementById("askButton");
  const chatMessages = document.getElementById("chatMessages");
  const modelToggle = document.getElementById("modelToggle");

  // Initialize event listeners
  setupEventListeners();

  function setupEventListeners() {
    // File upload handlers
    dropArea.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", handleFiles);

    // Drag and drop events
    ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
      dropArea.addEventListener(eventName, preventDefaults, false);
    });

    ["dragenter", "dragover"].forEach((eventName) => {
      dropArea.addEventListener(eventName, highlight, false);
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropArea.addEventListener(eventName, unhighlight, false);
    });

    dropArea.addEventListener("drop", handleDrop, false);

    // Question handling
    askButton.addEventListener("click", askQuestion);
    questionInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") askQuestion();
    });

    // Model toggle
    if (modelToggle) {
      modelToggle.addEventListener("change", (e) => {
        isOpenAIEnabled = e.target.checked;
        addMessage(
          "system",
          `Switched to ${isOpenAIEnabled ? "OpenAI" : "Hugging Face"} model`
        );
      });
    }
  }

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  function highlight() {
    dropArea.classList.add("highlight");
  }

  function unhighlight() {
    dropArea.classList.remove("highlight");
  }

  function handleDrop(e) {
    const dt = e.dataTransfer;
    handleFiles({ target: { files: dt.files } });
  }

  async function handleFiles(e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    currentFile = file;
    updateFileInfo(file);

    try {
      const formData = new FormData();
      formData.append("file", file);

      showLoading(true);
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(await getErrorMessage(response));
      }

      const data = await response.json();
      fileContent = data.data;
      addMessage(
        "assistant",
        `File "${file.name}" uploaded successfully. You can now ask questions about it.`
      );
    } catch (error) {
      addMessage("assistant", `Upload failed: ${error.message}`);
      console.error("Upload error:", error);
    } finally {
      showLoading(false);
    }
  }

  async function askQuestion() {
    const question = questionInput.value.trim();
    if (!question) {
      addMessage("assistant", "Please enter a question");
      return;
    }
    if (!currentFile || !fileContent) {
      addMessage("assistant", "Please upload a file first");
      return;
    }

    addMessage("user", question);
    questionInput.value = "";
    askButton.disabled = true;

    try {
      const requestData = {
        question: question,
        filename: currentFile.name,
        data_type: fileContent.type,
        content: fileContent,
        use_openai: isOpenAIEnabled,
      };

      showLoading(true);
      const response = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(await getErrorMessage(response));
      }

      const data = await response.json();
      displayAnswer(data);
    } catch (error) {
      addMessage("assistant", `Error: ${error.message}`);
      console.error("Ask error:", error);
    } finally {
      askButton.disabled = false;
      showLoading(false);
    }
  }

  // Helper functions
  function updateFileInfo(file) {
    fileInfo.innerHTML = `Selected file: <strong>${
      file.name
    }</strong> (${formatFileSize(file.size)})`;
    fileInfo.style.display = "block";
  }

  function displayAnswer(data) {
    const answerDiv = document.createElement("div");
    answerDiv.classList.add("message", "assistant-message");

    // Add confidence indicator for Hugging Face
    if (data.confidence && data.confidence < 1.0) {
      answerDiv.innerHTML = `
        <div class="answer">answer: ${data.answer}</div>
        <div class="confidence">Confidence: ${data.confidence}% (${data.model})</div>
      `;
    } else {
      answerDiv.innerHTML = `
        <div class="answer">${data.answer}</div>
        <div class="model-info">Generated by ${data.model}</div>
      `;
    }

    chatMessages.appendChild(answerDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  async function getErrorMessage(response) {
    try {
      const errorData = await response.json();
      return errorData.detail || response.statusText;
    } catch {
      return response.statusText;
    }
  }

  function showLoading(show) {
    // Implement your loading indicator
    if (show) {
      askButton.innerHTML =
        '<i class="fas fa-spinner fa-spin"></i> Processing...';
    } else {
      askButton.textContent = "Ask";
    }
  }

  function addMessage(role, content) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", `${role}-message`);
    messageDiv.textContent = content;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }
});