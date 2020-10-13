// Dragable object
var last_ComponentType_id = 0;
var last_Dynamic_id = 0;

var selectedOptions = ""

var arrayTreeIds = [];
var arrayListIds = [];
var component_count = 0 ;
var colorLevel1 = "#ffa726";
var colorLevel1a = "#ffd699";
var colorLevel2 = "#ffca28";
var colorLevel2a = "#ffee58";

var colorLevel3 = "#ffee58";
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

    var nodetext = document.createTextNode(component_name +'-'+component_count);

    var parentId = 0;
    //Principal Component

    if (component_name === "ComponentType" || component_name === "Dynamics"){

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
        subnodes.id = 'list'.concat(treenode_id);

        node.appendChild(subnodes);
        if(component_name === "Dynamics"){
            if(last_ComponentType_id > 0){
                var myUL = document.getElementById("list" + last_ComponentType_id);
                myUL.appendChild(node);
                clone.style.backgroundColor = colorLevel2;

                parentId = last_ComponentType_id;
            }else{
                alert("Please, add a ComponentType first");
            }

        }else{
            var myUL = document.getElementById("myUL");
            myUL.appendChild(node);
            clone.style.backgroundColor = colorLevel1;
        }

    } else{

        //set the name
        var node = document.createElement("li");
        node.id = treenode_id;
        node.append(nodetext);

        if(parent === "ComponentType"){
            parent = document.getElementById(last_ComponentType_id);
            parentId = last_ComponentType_id;
            node.style.backgroundColor = colorLevel1a;

        } else if (parent === "Dynamics"){
            parent = document.getElementById(last_Dynamic_id);
            parentId = last_Dynamic_id;
            node.style.backgroundColor = colorLevel2a;
        } else{
            return;
        }
        list = parent.querySelector("#list" + parentId);
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
    var language = document.getElementById('model_language').selectedOptions[0].value;
    showOverlay("/tools/dsl/details_model_overlay/" + language.toLowerCase() + "/" + newID +"/"+ component_name +"/"+ parent, true);
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
                alert(response);
            },
            error: function () {
                displayMessage("Error!", "errorMessage");
            }
        });
    } else{
        alert("Please provide a name");
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

// Operations with DrowDownList

function changeFunc(){
    var selectedOption = document.getElementById('model_language').selectedOptions[0].value;
    var container = document.getElementById("draggable_zone-container");
    var currentOption = container.getAttribute("option");

    if (currentOption.toLowerCase() !== selectedOption.toLowerCase()){
        //alert("currentOption:"+currentOption+"<>selectedOption:"+selectedOption);
        alert("If you change the selection the unsaved data will be lost!,\n are you sure?.")
    }

    var components = callData("getComponents",selectedOption);
    //alert(components);
    container.textContent = '';
    for(var key in components){
        if (components.hasOwnProperty(key)){
            var value = components[key];
            //<div id="{{ name }}" parent="{{ val "ob}}" class=ject-draggable shadow" draggable="true" ondragstart="onDragStart(event);">{{ name }}</div>
            //<div id="ComponentType" parent="" class="object-draggable shadow" draggable="true" ondragstart="onDragStart(event);">ComponentType</div>
            var new_div = document.createElement('div');
            var att = document.createAttribute("parent");
            att.value = value;
            new_div.id = key;
            new_div.setAttribute("parent", "value");
            new_div.innerHTML = key;
            new_div.className = "object-draggable shadow";
            new_div.draggable = "true";
            new_div.addEventListener("dragstart", onDragStart);
            new_div.setAttributeNode(att);
            container.appendChild(new_div);
        }
    }
    //components.foreach(comp){
     //   var btn = document.createElement("BUTTON");
      //  btn.innerHTML = "CLICK ME" + comp;
       // container.appendChild(btn);
    //};

    //Do something
    container.setAttribute("option", selectedOption);
    forceRedrawComponent(container)

    document.getElementById("test").innerHTML = "You selected: " + selectedOption;

}

function forceRedrawComponent(component){
    var display = component.style.display;
    component.style.display = 'none';
    var offset = component.offsetHeight;
    component.style.display = display;

}
function callData(subUrl,argument){
    var dict = Object();
    doAjaxCall({
        async: false,
        type: 'GET',
        dataType: "json",
        url: "/tools/dsl/getComponents/"+argument,
        success: function (response) {

            var components = JSON.parse(response); //JSON.parse(JSON.stringify(response));

            for(var key in components){
                if (components.hasOwnProperty(key)){
                    var value = components[key];
                    dict[key] = value;
                }
            }
        },
        error: function () {
            alert("Error!, No data available!");
        }
    });
    return JSON.parse(JSON.stringify(dict));;
}