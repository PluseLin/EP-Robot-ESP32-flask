var script=document.createElement("script");  
script.type="text/javascript";  
script.src="jquery.js"; 

$(document).ready(function(){
    $(".btn").click(function(){
        var button_id=$(this).attr("id");
        var data={
            "action":button_id,
        };
        $.ajax({
            type:"POST",
            cache:false,
            data:JSON.stringify(data),
            contentType:'application/json;charset=UTF-8',
            dataType:'json',
            async:true,
            success:function(ret){
                if(ret.type="get_temp"){
                    $("#temperature").text(ret.data);
                }
                else{
                    window.location.reload();
                }
            },
            error:function(xhr,type){

            }
        });
    })
})