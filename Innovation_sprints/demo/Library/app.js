// Function to dynamically add divs to the body
function addDivToBody(id, content) {
    const div = document.createElement('div');
    div.id = id;
    div.innerHTML = content;
    document.body.appendChild(div);
}

// Event listeners for button clicks to load different sections
document.getElementById('loadHeader').addEventListener('click', () => {
    import('./module/header.js').then(module => {
        module.addHeaderDiv(addDivToBody);
    });
});

document.getElementById('loadFooter').addEventListener('click', () => {
    import('./module/footer.js').then(module => {
        module.addFooterDiv(addDivToBody);
    });
});
