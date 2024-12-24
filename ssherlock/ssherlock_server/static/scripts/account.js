/**
 * Displays a success popup with the given message.
 * @param {string} message - The message to display in the popup.
 */
function showSuccessPopup(message) {
    const popup = document.createElement('div');
    popup.id = 'confirmationPopup';
    popup.className = 'fixed inset-0 flex items-center justify-center bg-black bg-opacity-50';
    const innerPopup = document.createElement('div');
    innerPopup.className = 'bg-gray-800 p-5 rounded-lg shadow-lg text-white';
    const messageParagraph = document.createElement('p');
    messageParagraph.id = 'confirmationMessage';
    messageParagraph.className = 'mb-4';
    messageParagraph.textContent = message;
    innerPopup.appendChild(messageParagraph);
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'flex justify-end space-x-4';
    const okButton = document.createElement('button');
    okButton.className = 'bg-green-500 hover:bg-green-600 mt-2 p-1.5 rounded';
    okButton.textContent = 'OK';
    okButton.onclick = () => popup.remove();
    buttonContainer.appendChild(okButton);
    innerPopup.appendChild(buttonContainer);
    popup.appendChild(innerPopup);
    document.body.appendChild(popup);
}

/**
 * Initializes the success popup display logic on page load.
 */
document.addEventListener('DOMContentLoaded', function() {
    if ("{{ success }}") {
        setTimeout(() => {
            showSuccessPopup("{{ success }}");
        }, 500);
    }
});
