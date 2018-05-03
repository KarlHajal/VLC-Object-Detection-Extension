function descriptor()
    return {
        title = "Object Detector";
        version = "0.1";
        decription = [[ 
Object Detector.

Object Detector is a VLC extension that allows a user to search for objects in a video file.
        ]];
        capabilities = {"menu"}
    }
end

function activate()
    USER = "karl"
    local_directory = "/home/" .. USER .. "/.local/share/vlc/lua/extensions/"
    vlc.msg.info("Object Detector activating")
    create_dialog()
end

function deactivate()
    vlc.deactivate()
end

function close()
    os.execute("rm " .. local_directory .. "object_detection_output.txt")
    os.execute("rm " .. local_directory .. "frame*.jpg")
    vlc.deactivate()
    vlc.msg.info("Object Detector closed")
end

function meta_changed()
end

function create_dialog()
    dlg = vlc.dialog(descriptor().title)
    dlg:add_label("<b>Search for Object:</b>", 1, 1, 1, 1)
    object_name = dlg:add_text_input("", 2, 1, 4, 1)
    dlg:add_label("<b>Search in Subtitles:</b>", 1, 2, 1, 1)
    subtitle_text = dlg:add_text_input("", 2, 2, 4, 1)
    dlg:add_label("<b>Start Time:</b>",1, 3, 1, 1)
    start_time_hours_text = dlg:add_text_input("0", 2, 3, 1, 1)
    dlg:add_label("<b>h</b>", 3, 3, 1, 1)
    start_time_minutes_text = dlg:add_text_input("0", 4, 3, 1, 1)
    dlg:add_label("<b>m</b>", 5, 3, 1, 1)
    start_time_seconds_text = dlg:add_text_input("0", 6, 3, 1, 1)
    dlg:add_label("<b>s</b>", 7, 3, 1, 1)
    dlg:add_button("Search", click_SEARCH, 2, 4, 1, 1)
    dlg:add_button("Stop", click_STOP, 4, 4, 1, 1)
    result_label = dlg:add_label("", 6, 4, 1, 1)

    vlc.msg.info("Object Detector dialog created")
end

function click_SEARCH()
    local f = io.open(local_directory .. "object_detection_output.txt", "r")
    if f ~= nil then
        io.close(f)
        os.remove(local_directory .. "object_detection_output.txt")
    end
    
    local item = vlc.input.item()
    local video_file_directory = item:uri()
    video_file_directory = string.gsub(video_file_directory, '^file://', '')
    video_file_directory = string.gsub(video_file_directory, '%%20', '\\ ')
    object_detection_script_directory = local_directory .. "video_object_detection.py"
    
    local time = tostring(tonumber(start_time_hours_text:get_text())*3600 + tonumber(start_time_minutes_text:get_text())*60 + tonumber(start_time_seconds_text:get_text()))

    vlc.msg.info("Object Detector Starting Search for " .. object_name:get_text() .. " in " .. video_file_directory)
    cmd = "python3 " .. object_detection_script_directory .. " " .. video_file_directory .. " " .. object_name:get_text() .. " " .. time .. " 0"
    vlc.msg.info("Running command: " .. cmd)
   
    result_label:set_text("<b>Searching</b>")
    os.execute(cmd)
    
    local f = io.open(local_directory .. "object_detection_output.txt", "r")
    if f ~= nil then  
        result_label:set_text("<b>Object Found!</b>")
        result_frame = f:read "*line"
        dlg:add_image(local_directory .. "frame".. result_frame .. ".jpg", 2,5,5,5)
        io.close(f)
        os.remove(local_directory .. "object_detection_output.txt")
    else
        result_label:set_text("<b>No Result</b>")
    end
end

function click_STOP()
    vlc.msg.info("Object Detector Stopping the Search")
    result_label:set_text("<b></b>")
end
