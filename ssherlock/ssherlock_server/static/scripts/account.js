/**
 * Displays a success popup with the given message.
 * @param {string} message - The message to display in the popup.
 */
function showSuccessPopup(message) {
    // Create a popup element to display the success message
    const popup = document.createElement('div');
    popup.id = 'confirmationPopup';
    popup.className = 'fixed inset-0 flex items-center justify-center bg-black bg-opacity-50';
    // Create the inner popup container
    const innerPopup = document.createElement('div');
    innerPopup.className = 'bg-gray-800 p-5 rounded-lg shadow-lg text-white';
    // Create a paragraph element for the message
    const messageParagraph = document.createElement('p');
    messageParagraph.id = 'confirmationMessage';
    messageParagraph.className = 'mb-4';
    messageParagraph.textContent = message;
    innerPopup.appendChild(messageParagraph);
    // Create a container for the buttons
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'flex justify-end space-x-4';
    // Create an OK button to close the popup
    const okButton = document.createElement('button');
    okButton.className = 'bg-green-500 hover:bg-green-600 mt-2 p-1.5 rounded';
    okButton.textContent = 'OK';
    okButton.onclick = () => popup.remove();
    buttonContainer.appendChild(okButton);
    innerPopup.appendChild(buttonContainer);
    popup.appendChild(innerPopup);
    document.body.appendChild(popup); // Append the popup to the body
}

/**
 * Initializes the success popup display logic on page load.
 * Displays the success message if available.
 */
document.addEventListener('DOMContentLoaded', function() {
    if ("{{ success }}") {
        setTimeout(() => {
            showSuccessPopup("{{ success }}");
        }, 500);
    }
});
