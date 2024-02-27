let listState = [];
const STATE_KEY = "to-do-list";

function addItem() {
    const input = document.getElementById("input-item");
    const item = input.value;
    if (item === "") {
        alert("Please enter again");
        return;
    }

    listState.push({
        text: item,
        checked: false,
    });

    const newItem = `<li><input type="checkbox" id="check"><label>${item}</label><button class="delete-button">X</button></li>`;
    document.getElementById("list").insertAdjacentHTML("beforeend", newItem);
    input.value = "";

    const deleteButtons = document.querySelectorAll(".delete-button");
    deleteButtons.forEach(function (button) {
        button.addEventListener("click", deleteItem);
    });

    document
        .querySelectorAll('input[type="checkbox"], label')
        .forEach(function (element) {
            element.addEventListener("click", checkItem);
        });

    saveState();
}

function deleteItem() {
    const listItem = this.parentNode;
    const idx = Array.from(listItem.parentNode.childNodes).indexOf(listItem);
    listState = listState.filter((_, i) => i !== idx);
    listItem.remove();
    saveState();
}

function checkItem() {
    console.log(this.tagName);
    const parent = this.parentNode;
    const check_box = parent.childNodes[0];
    const label = parent.childNodes[1];
    //console.log(check_box.tagName);
    setTimeout(() => {
        check_box.checked = !check_box.checked;
    }, 0);
    label.classList.toggle("checked-item");

    const idx = Array.from(parent.parentNode.childNodes).indexOf(parent);
    listState[idx].checked = !listState[idx].checked;
    saveState();
}

function loadState() {
    const listJSON = localStorage.getItem(STATE_KEY);
    return listJSON ? JSON.parse(listJSON) : [];
}

function initList() {
    listState = loadState();
    if (listState === null) return;
    const ul = document.getElementById("list");
    for (const item of listState) {
        const checkedClass = item.checked ? 'class="checked-item"' : "";
        const newItem = `<li><input type="checkbox" id="check" ${
            item.checked ? "checked" : ""
        }><label ${checkedClass}>${
            item.text
        }</label><button class="delete-button">X</button></li>`;
        ul.insertAdjacentHTML("beforeend", newItem);
    }

    document
        .querySelectorAll('input[type="checkbox"], label')
        .forEach(function (element) {
            element.addEventListener("click", checkItem);
        });

    document.querySelectorAll(".delete-button").forEach(function (button) {
        button.addEventListener("click", deleteItem);
    });
}

function saveState() {
    localStorage.setItem(STATE_KEY, JSON.stringify(listState));
}

initList();

const addButton = document.getElementById("add");
addButton.addEventListener("click", addItem);

const form = document.getElementById("input-wrapper");
form.addEventListener("click", (e) => {
    e.preventDefault();
});
