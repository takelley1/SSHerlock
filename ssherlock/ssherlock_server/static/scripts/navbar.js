/**
 * Toggles the visibility of the account dropdown menu in the navbar.
 */
$(document).ready(function() {
    $('#accountButton').on('click', function(event) {
        event.preventDefault(); // Prevent default action
        event.stopPropagation();
        $('#accountDropdown').toggleClass('hidden');
    });
});
