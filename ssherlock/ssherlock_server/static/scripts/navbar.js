/**
 * Toggles the visibility of the account dropdown menu in the navbar.
 * This function is called when the document is fully loaded.
 */
$(document).ready(function() {
    $('#accountButton').on('click', function(event) {
        event.preventDefault(); // Prevent default action
        event.stopPropagation(); // Stop the event from propagating to other elements
        $('#accountDropdown').toggleClass('hidden'); // Toggle the hidden class to show/hide the dropdown
    });
});
