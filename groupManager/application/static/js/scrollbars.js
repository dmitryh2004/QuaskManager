function setScrollBar(parentId, childId) {
    var scroll_height = document.getElementById(parentId).offsetHeight;
    var window_height = window.innerHeight;
    var footer = document.getElementsByClassName("footer")[0];
    console.log(footer);
    var footer_height = footer.offsetHeight;
    var max_height = window_height - footer_height - 30;
    console.log("scroll_height = " + scroll_height + ", max = " + max_height);

    if (scroll_height > max_height) {
        document.getElementById(childId).style["overflow-y"] = "scroll";
        document.getElementById(parentId).style["height"] = "calc(100% - 4em - 30px)";
        document.getElementById(childId).style["height"] = "calc(100% - 30px)";
    }
    else {
        document.getElementById(childId).style["overflow-y"] = "hidden";
    }
}

function setScrollBarMultiple(parentId, childIds) {
    var scroll_height = document.getElementById(parentId).offsetHeight;
    var window_height = window.innerHeight;
    var footer = document.getElementsByClassName("footer")[0];
    console.log(footer);
    var footer_height = footer.offsetHeight;
    var max_height = window_height - footer_height - 30;
    console.log("scroll_height = " + scroll_height + ", max = " + max_height);

    if (scroll_height > max_height) {
        document.getElementById(parentId).style["height"] = "calc(100% - 4em - 30px)";
        childIds.forEach(childId => {
            document.getElementById(childId).style["overflow-y"] = "scroll";
            document.getElementById(childId).style["height"] = "calc(100% - 30px)";
        });
    }
    else {
        childIds.forEach(childId => {
            document.getElementById(childId).style["overflow-y"] = "hidden";
        });
    }
}