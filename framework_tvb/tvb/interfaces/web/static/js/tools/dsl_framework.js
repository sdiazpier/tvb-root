// Dragable object
var last_ComponentType_id = 0;
var last_Dynamic_id = 0;

var selectedOptions = ""
var working_folder = "";

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
            clone.style.backgroundColor = colorLevel1a;

        } else if (parent === "Dynamics"){
            parent = document.getElementById(last_Dynamic_id);
            parentId = last_Dynamic_id;
            clone.style.backgroundColor = colorLevel2a;
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
function removeLastDropped(removexml){
    if(arrayListIds !== undefined && arrayListIds.length > 0){
        component_count -=1;
        document.getElementById(arrayTreeIds.pop()).remove();
        document.getElementById(arrayListIds.pop()).remove();
    } else{
        last_ComponentType_id = 0;
        last_Dynamic_id = 0;
    }

    if( removexml == true){
        getXML();
    }
}

function removeAlltDropped(){
    while(arrayListIds !== undefined && arrayListIds.length > 0){
        removeLastDropped(false);
    }
    getXML();
}

function prepareHeader(){
    var header = {};
    header['name']= document.getElementById('model_name').value;
    header['description']= document.getElementById('model_description').value;
    header['language']= document.getElementById('model_language').selectedOptions[0].value;
    header['folder']= document.getElementById('working_folder').value;
    working_folder = header['folder'];
    return JSON.parse(JSON.stringify(header));
}
function overlaySubmit(formToSubmitId, backPage) {
    var submitableData = prepareHeader();
    //var valor = submitableData['name'];
    if (submitableData['name'].length > 0 ){
        doAjaxCall({
            async: false,
            type: 'POST',
            url: "/tools/dsl/convertdata",
            data: submitableData,
            success: function (response) {
                //alert(response);
                var result = confirm(response + "\nDo you want to see the generated model?.");
                if(result == true){

                    var content = "";
                    var reader = new FileReader();
                    const file = working_folder+'/'+submitableData['name'];

                    reader.addEventListener('load',function(event){
                      content = event.target.result;
                    });
                    reader.readAsText(file,"UTF-8");
                    alert(content);
                }

            },
            error: function () {
                displayMessage("Error!", "errorMessage");
            }
        });
    } else{
        alert("Please provide a Model Name");
    }

}

function getmodels(){
    var header = {};
    header['model_location_option']= document.getElementById('model_location_option').selectedOptions[0].value;
    header['folder']= document.getElementById('working_folder').value;
    working_folder = header['folder'];
    var submitableData = JSON.parse(JSON.stringify(header));
    if(submitableData['model_location_option'].length > 0 ){
        doAjaxCall({
            async: false,
            type: 'POST',
            url: "/tools/dsl/getmodels",
            data: submitableData,
            success: function (response) {

                var items = JSON.parse(response); //JSON.parse(JSON.stringify(response));

                document.getElementById('working_folder').value = items["folder"];

                //cleanning old elements
                var list = document.getElementById("listing");
                while(list.firstChild){
                    list.removeChild(list.firstChild);
                }

                //Create new ones into the list
                for (var i = 0; i < items["files"].length; i++) {
                    var item = document.createElement('li');

                    // Set its contents:
                    item.innerHTML = items["files"][i]//item;
                    //item.className = ""
                    //item.addEventListener("click", convertmodel(item.innerHTML););

                    // Add it to the list:
                    list.appendChild(item);
                }
            },
            error: function () {
                displayMessage("Error!", "errorMessage");
            }
        });

    } else{
        alert("Please select a predefined location");
    }
}
function convertmodel(a){
    alert(a+ " was clicked");
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

    //Get XML content from the server
    getXML();
}

// Operations with DrowDownList

function changeFunc(){
    var selectedOption = document.getElementById('model_language').selectedOptions[0].value;
    var parent_container = document.getElementById("parent-draggable_zone");
    var container = document.getElementById("draggable_zone-container");
    var currentOption = container.getAttribute("option");


    if(selectedOption === "None"){
        parent_container.style.display = "none";
    } else {
        parent_container.style.display = "block";
    }

    if (currentOption !== "" && currentOption.toLowerCase() !== selectedOption.toLowerCase()){
        //alert("currentOption:"+currentOption+"<>selectedOption:"+selectedOption);
        var result = confirm("All data will be lost!,\n Are you sure?.");
        if (result == true) {
            removeAlltDropped();

        } else{
            selectedOption = currentOption;
            document.getElementById('model_language').value = selectedOption;
        }
    }

    var components = getComponents("getComponents",selectedOption);
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

    //Do something
    container.setAttribute("option", selectedOption);
    forceRedrawComponent(container);
}

function forceRedrawComponent(component){
    var display = component.style.display;
    component.style.display = 'none';
    var offset = component.offsetHeight;
    component.style.display = display;

}
function getComponents(subUrl,argument){
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
    return JSON.parse(JSON.stringify(dict));
}

function getXML(){
    var submitableData = prepareHeader();
    if (submitableData['name'].length > 0 ){
        doAjaxCall({
            async: false,
            type: 'POST',
            dataType: "json",
            url: "/tools/dsl/getxml",
            data: submitableData,
            success: function (response) {

                if(response.length > 0){
                    var area = document.getElementById("Textarea");
                    area.innerHTML = response;
                } else{
                    alert("XML content was not nice!");
                }
            },
            error: function () {
                alert("Error! processing xml in the server");
            }
        });
    } else{
        alert("XML Header is not ready yet");
    }
}

/**
* Operations with files
*/
function changeLocation(){
    var selectedOption = document.getElementById('model_location').selectedOptions[0].value;

}
function select_folder(event){

    var files = event.target.files;
    var path = files[0].webkitRelativePath;
    var folder =  path.split("/");
    document.getElementById("working_folder").value = path;

    var list = document.getElementById("listing");

    while(list.firstChild){
        list.removeChild(list.firstChild);
    }

    for (var i = 0; i < files.length; i++) {
        var item = document.createElement('li');

        // Set its contents:
        item.appendChild(document.createTextNode("HOla"));//files[i]

        // Add it to the list:
        list.appendChild(item);
    }
}