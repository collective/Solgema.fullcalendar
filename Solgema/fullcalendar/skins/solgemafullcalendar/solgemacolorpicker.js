function initColorpicker() {
    jq(".colorinput").each( function(i, elem) {
        var name = jq(elem).attr('name')
        jq(elem).ColorPicker({
	    onChange: function(hsb, hex, rgb, el) {
		jq('input[name='+name+']').val('#' + hex);
                jq('input[name='+name+']').css('backgroundColor', '#' + hex);
	    },
	    onSubmit: function(hsb, hex, rgb, el) {
		jq(el).val('#' + hex);
                jq(el).css('backgroundColor', '#' + hex);
		jq(el).ColorPickerHide();
	    },
	    onBeforeShow: function () {
		jq(this).ColorPickerSetColor(this.value);
	    }
        })
    });
    jq(".colorinput").change( function(){
	    jq(this).ColorPickerSetColor(this.value);
    });
};

jq(document).ready(function() {
    jq(initColorpicker);
});

