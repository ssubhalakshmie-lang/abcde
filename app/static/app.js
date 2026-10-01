const actionDetails = {
  ask: {
    title: "Ask anything",
    eyebrow: "WHAT'S ON YOUR MIND?",
    placeholder: "Which is the largest ocean?",
    intro: "Curiosity is a good place to start. Ask a question and build from there.",
    button: "Get an answer",
    response: "Here's what I found",
  },
  simplify: {
    title: "Simplify a concept",
    eyebrow: "WHAT WOULD YOU LIKE TO UNDERSTAND?",
    placeholder: "The water cycle, in simple terms",
    intro: "Bring a big idea down to earth, one clear explanation at a time.",
    button: "Make it clear",
    response: "A simpler explanation",
  },
  quiz: {
    title: "Generate a quiz",
    eyebrow: "WHAT TOPIC SHOULD WE PRACTICE?",
    placeholder: "The Pythagorean theorem",
    intro: "A few good questions can show you what has really clicked.",
    button: "Build my quiz",
    response: "Your practice quiz",
  },
  path: {
    title: "Build a learning path",
    eyebrow: "WHAT DO YOU WANT TO LEARN?",
    placeholder: "SQL, from beginner to advanced",
    intro: "Turn a new interest into a steady, practical plan.",
    button: "Plan my learning",
    response: "Your learning path",
  },
  summarize: {
    title: "Summarize text",
    eyebrow: "PASTE A PASSAGE TO GET STARTED",
    placeholder: "Paste a passage, article excerpt, or set of notes...",
    intro: "Pull the important ideas out of a longer reading.",
    button: "Find the key ideas",
    response: "The key ideas",
  },
};

const form = document.querySelector("#study-form");
const input = document.querySelector("#study-input");
const submitButton = document.querySelector("#submit-button");
const submitLabel = document.querySelector("#submit-label");
const responsePanel = document.querySelector("#response-panel");
const responseBody = document.querySelector("#response-body");
const responseFooter = document.querySelector("#response-footer");
const responseTitle = document.querySelector("#response-title");
const modeIndicator = document.querySelector("#mode-indicator");
const modeLabel = document.querySelector("#mode-label");
const navButtons = [...document.querySelectorAll("[data-action]")];
let selectedAction = "ask";
let latestAnswer = "";

function selectAction(action) {
  selectedAction = action;
  const details = actionDetails[action];
  document.querySelector("#current-tool").textContent = details.title;
  document.querySelector("#input-label").textContent = details.eyebrow;
  document.querySelector("#intro-copy").textContent = details.intro;
  document.querySelector("#submit-label").textContent = details.button;
  input.placeholder = details.placeholder;
  responseTitle.textContent = details.response;
  responsePanel.hidden = true;
  document.querySelector("#suggestions").hidden = action === "summarize";
  navButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.action === action && button.classList.contains("tool-link"));
  });
}

navButtons.forEach((button) => {
  button.addEventListener("click", () => {
    selectAction(button.dataset.action);
    if (button.classList.contains("desk-item")) {
      document.querySelector("#study-input").focus();
      document.querySelector("#study-form").scrollIntoView({ behavior: "smooth", block: "center" });
    }
  });
});

document.querySelectorAll(".suggestion-chip").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt;
    input.focus();
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const content = input.value.trim();
  if (!content) {
    input.focus();
    return;
  }

  submitButton.disabled = true;
  submitLabel.textContent = "Thinking...";
  responsePanel.hidden = false;
  responseBody.classList.add("loading-copy");
  responseBody.textContent = "Putting a clear answer together...";
  responseFooter.textContent = "";

  try {
    const response = await fetch("/api/study", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: selectedAction,
        content,
        level: document.querySelector("#level-select").value,
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "The request could not be completed.");

    latestAnswer = result.answer;
    responseBody.textContent = result.answer;
    responseBody.classList.remove("loading-copy");
    responseFooter.textContent = result.mode === "ai"
      ? "AI-generated study support. Check important facts against your course materials."
      : "Demo response. Configure an AI model for tailored explanations and generated content.";
  } catch (error) {
    latestAnswer = "";
    responseBody.classList.remove("loading-copy");
    responseBody.textContent = error.message || "Something went wrong. Please try again.";
    responseFooter.textContent = "Your work is still here. Try again in a moment.";
  } finally {
    submitButton.disabled = false;
    submitLabel.textContent = actionDetails[selectedAction].button;
  }
});

document.querySelector("#copy-button").addEventListener("click", async (event) => {
  if (!latestAnswer) return;
  try {
    await navigator.clipboard.writeText(latestAnswer);
    event.currentTarget.textContent = "Copied";
    window.setTimeout(() => { event.currentTarget.textContent = "Copy"; }, 1500);
  } catch {
    event.currentTarget.textContent = "Copy unavailable";
  }
});

fetch("/api/status")
  .then((response) => response.json())
  .then(({ mode }) => {
    modeIndicator.dataset.mode = mode;
    modeLabel.textContent = mode === "ai" ? "AI connected" : "Demo mode";
  })
  .catch(() => {
    modeLabel.textContent = "Status unavailable";
  });