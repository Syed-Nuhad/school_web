(function () {
  function start(jq) {
    jq(function () {
      var $grade = jq("#id_grade");
      if (!$grade.length) return;

      var url = new URL(window.location.href);
      var urlGrade = url.searchParams.get("grade"); // grade we already loaded for

      function triggerReload() {
        var val = ($grade.val() || "").toString();
        if (!val) return;
        if (urlGrade && urlGrade === val) return;   // <-- stop the reload loop

        var termVal = (jq("#id_term").val() || "").toString();
        url.searchParams.set("grade", val);
        if (termVal) url.searchParams.set("term", termVal);
        window.location.assign(url.toString());
      }

      // Plain <select>
      $grade.on("change", function (e) {
        // ignore programmatic/init changes that select2 fires
        if (e && e.originalEvent === undefined && typeof jq.fn.select2 === "function") return;
        triggerReload();
      });

      // Select2
      if ($grade.on) $grade.on("select2:select", triggerReload);
    });
  }
  if (window.django && django.jQuery) start(django.jQuery);
  else if (window.jQuery) start(window.jQuery);
})();
