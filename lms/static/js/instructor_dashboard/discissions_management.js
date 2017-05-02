(function() {
    var DiscussionsManagement;

    DiscussionsManagement = (function() {
        function DiscussionsManagement($section) {
            this.$section = $section;
            this.$section.data('wrapper', this);
        }

        DiscussionsManagement.prototype.onClickTitle = function() {};

        return DiscussionsManagement;
    })();

    window.InstructorDashboard.sections.DiscussionsManagement = DiscussionsManagement;
}).call(this);
