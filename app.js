const form = document.querySelector("#todo-form");
const input = document.querySelector("#todo-input");
const status = document.querySelector("#status");
const list = document.querySelector("#todo-list");

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const value = input.value.trim();
  if (!value) {
    status.textContent = "Enter a task before adding.";
    input.focus();
    return;
  }

  const item = document.createElement("li");
  item.textContent = value;
  list.appendChild(item);

  status.textContent = `Added "${value}".`;
  input.value = "";
  input.focus();
});
