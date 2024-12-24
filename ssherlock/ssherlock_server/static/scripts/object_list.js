/**
 * Initializes the DataTable for the object list table.
 * This function is called when the document is fully loaded.
 */
$(document).ready(function () {
    $('#object_list_table').DataTable();
});

/**
 * Displays a custom confirmation popup for deleting an object.
 * @param {string} objectName - The name of the object to delete.
 * @param {string} deleteUrl - The URL to redirect to for deletion.
 */
function showConfirmationPopup(objectName, deleteUrl) {
    // Set the confirmation message with the object name
    $('#confirmationMessage').text(`Are you sure you want to delete this ${objectName}?`);
    $('#confirmButton').off('click').on('click', function () {
        window.location.href = deleteUrl;
    });
    // Show the confirmation popup
    $('#confirmationPopup').removeClass('hidden');
}

/**
 * Hides the confirmation popup when the cancel button is clicked.
 */
$('#cancelButton').on('click', function () {
    // Hide the confirmation popup
    $('#confirmationPopup').addClass('hidden');
});
