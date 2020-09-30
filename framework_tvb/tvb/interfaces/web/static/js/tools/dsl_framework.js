// Dragable object
var last_ComponentType_id = 0;
var last_Dynamic_id = 0;

var arrayTreeIds = [];
var arrayListIds = [];
var component_count = 0 ;

function onDragStart(event) {
    event.dataTransfer.setData('text/plain', event.target.id);
}

// fires when the dragged element is over the drop target
function onDragOver(event) {
    event.preventDefault();
}

function createId(obj, seed){
    return obj.toString() + seed.toString();
}


// fires when the dragged element is dropped on the drop target
function onDrop(event) {
    event.preventDefault();
    component_count +=1;
    var component_name = event.dataTransfer.getData('text');
    var clone = document.getElementById(component_name).cloneNode(true);
    clone.id = createId(component_name,(new Date()).getMilliseconds());

    var treenode_id = component_count;

    var parent = clone.getAttribute('parent');


    if(parent === "Dynamics" && last_Dynamic_id == 0){
        alert("There is not Dynamic Component!" + last_Dynamic_id);
        return;
    }
    if(parent === "ComponentType" && last_ComponentType_id == 0){
        alert("There is not Principal Component!");
        return;
    }

    //We clone a draggable object to drop it in a list, with NAME and ID=name-second
    //We need also add new node with new ID to the Treenode.


     //Nodes in the tree has different numeration. Every object in the list or treenode has identification
    if(component_name === "ComponentType"){
        last_ComponentType_id = component_count;
    }
    if(component_name === "Dynamics"){
        last_Dynamic_id = component_count;
    }

    var myUL = document.getElementById("myUL");
    var nodetext = document.createTextNode(component_name +'-'+component_count);

    var parentId = "none"
    //Principal Component
    if (parent === "none"){

        //prepare main component
        var span = document.createElement("span");
        span.className = "caret";
        span.appendChild(nodetext);
        span.addEventListener("click", function() {
          this.parentElement.querySelector(".nested").classList.toggle("active");
          this.classList.toggle("caret-down");
        });


        //set the name
        var node = document.createElement("li");
        node.id = treenode_id;
        node.append(span);

        //set a container
        var subnodes = document.createElement("UL");
        subnodes.className = "nested";
        subnodes.id = 'list';

        node.appendChild(subnodes);
        myUL.appendChild(node);
        clone.style.backgroundColor = "yellow";

    } else{
        //document.getElementById(id).getElementsByTagName('caret')
        if(parent === "ComponentType"){
            parent = document.getElementById(last_ComponentType_id);
            parentId = last_ComponentType_id;
        } else if (parent === "Dynamics"){
            parent = document.getElementById(last_Dynamic_id);
            parentId = last_Dynamic_id;
        } else{
            return;
        }

        //set the name
        var node = document.createElement("li");
        node.id = treenode_id;
        node.append(nodetext);
        //parent.append(node);

        list = parent.querySelector('#list');
        list.appendChild(node);
    }

    //If everything was ok, the draggable object is dropped
    event.target.appendChild(clone);
    showProperties(treenode_id, component_name, parentId );

    // TODO: Add principal component to the controller
    arrayListIds.push(clone.id);
    arrayTreeIds.push(treenode_id);

}

function clearTrash(){
    var div = document.getElementById('trash');
    while(div.firstChild){
        div.removeChild(div.firstChild);
    }
}

//Treeview operations
var toggler = document.getElementsByClassName("caret");
var i;

for (i = 0; i < toggler.length; i++) {
    toggler[i].addEventListener("click", function() {
        this.parentElement.querySelector(".nested").classList.toggle("active");
        this.classList.toggle("caret-down");
    });
}


// Popup Windows
function showProperties(newID, component_name, parent ){
    closeOverlay(); // If there was overlay opened, just close it
    showOverlay("/tools/dsl/details_model_overlay/" + newID +"/"+ component_name +"/"+ parent, true);
}

// OPERATIONS WITH INDEXES
function updateIndexes(concept, oper){
    switch(concept){
        case "ComponentType":
            last_ComponentType_id = last_ComponentType_id + oper;
            break;
        case "Dynamics":
            last_Dynamic_id = last_Dynamic_id + oper;
            break;
    }
}

// TODO: FUNCTIONS TO MOVE IN A OPERATIONS FILE
function removeLastDropped(){
    if(arrayListIds !== undefined && arrayListIds.length > 0){
        component_count -=1;
        document.getElementById(arrayTreeIds.pop()).remove();
        document.getElementById(arrayListIds.pop()).remove();
    } else{
        last_ComponentType_id = 0;
        last_Dynamic_id = 0;
    }
}

function removeAlltDropped(){
    while(arrayListIds !== undefined && arrayListIds.length > 0){
        removeLastDropped();
    }
}

function overlaySubmit(formToSubmitId, backPage) {
    var submitableData = {};

    submitableData['name']= document.getElementById('model_name').value;
    submitableData['description']= document.getElementById('model_description').value;
    submitableData['language']= document.getElementById('model_language').selectedOptions[0].value;
    var valor = submitableData['name'];

    if (valor.length > 0 ){
        doAjaxCall({
            async: false,
            type: 'POST',
            url: "/tools/dsl/convertdata",
            data: submitableData,
            success: function (response) {
                displayMessage("Data successfully exported!");
                alert("Data successfully exported!");
            },
            error: function () {
                displayMessage("Error!", "errorMessage");
            }
        });
    } else{
        alert("Incomplete fields");
    }

}

/**
 * Used from DataType(Group) overlay to store changes in meta-data.
 */
function overlaySubmitPart(formToSubmitId, backPage) {

    var submitableData = getSubmitableData(formToSubmitId, false);
    const id = submitableData['id'];
    const parent = submitableData['parent'];

    doAjaxCall({
        async: false,
        type: 'POST',
        url: "/tools/dsl/updatedata",
        data: submitableData,
        success: function (response) {
            displayMessage("Data successfully stored! " + response);
            closeAndRefreshTreeView(id, parent, response);
        },
        error: function () {
            displayMessage("Error!", "errorMessage");
        }
    });
}

// Operations between pages
/**
 * Close overlay and refresh backPage.
 */
function closeAndRefreshTreeView(id, parent, response) {

    var spanList = document.getElementById(id).getElementsByClassName("caret");
    if (spanList.length == 1){
        document.getElementById(id).getElementsByClassName('caret')[0].innerHTML = response;
    }else{
        document.getElementById(id).innerText = response;
    }
    closeOverlay();
}

