$( document ).ready(function() {
    // Choose the default tab based on the user's OS.
    var os='windows';
    if (navigator.platform.toUpperCase().indexOf('MAC')!==-1) {
        os = 'osx';
    } else if (navigator.platform.toUpperCase().indexOf('LINUX')!==-1) {
        os = 'linux';
    }
    $('#os_tab a[href="#' + os + '"]').tab('show')
});

function SimpleCtrl($scope) {
    $scope.latest_version = 'v2.5.8';
}
