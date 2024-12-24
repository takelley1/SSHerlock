/**
 * Initializes the DataTable for the object list table.
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
    $('#confirmationMessage').text(`Are you sure you want to delete this ${objectName}?`);
    $('#confirmButton').off('click').on('click', function () {
        window.location.href = deleteUrl;
    });
    $('#confirmationPopup').removeClass('hidden');
}

/**
 * Hides the confirmation popup when the cancel button is clicked.
 */
$('#cancelButton').on('click', function () {
    $('#confirmationPopup').addClass('hidden');
});
