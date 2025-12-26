local http = require("socket.http")
local ltn12 = require("ltn12")
local json = require("dkjson")
local lfs = require("lfs")

-- Configuration
local config = {
    webhookUrl = "YOUR_DISCORD_WEBHOOK_URL",  -- Replace with your Discord webhook URL
    scanPaths = {
        "C:\\Program Files (x86)\\Steam\\steamapps\\common",  -- Common Steam games directory
        "C:\\Program Files\\Epic Games",  -- Common Epic Games directory
        -- Add more paths as needed
    },
    fileExtensions = {
        ".lua", ".txt", ".json", ".cfg", ".ini"  -- Common text-based file types to scan
    },
    keywords = {
        "brainrot", "cheat", "hack", "exploit", "script"  -- Keywords to search for
    },
    maxFileSize = 5 * 1024 * 1024,  -- 5MB max file size to scan
    cooldown = 1  -- Seconds to wait between Discord webhook sends
}

-- Function to send message to Discord
local function sendToDiscord(message)
    local payload = {
        content = message,
        username = "Brainrot Scanner",
        avatar_url = "https://i.imgur.com/example.png"  -- Optional: Replace with your bot's avatar
    }
    
    local payloadJson = json.encode(payload)
    local response_body = {}
    
    local res, code, response_headers = http.request{
        url = config.webhookUrl,
        method = "POST",
        headers = {
            ["Content-Type"] = "application/json",
            ["Content-Length"] = #payloadJson
        },
        source = ltn12.source.string(payloadJson),
        sink = ltn12.sink.table(response_body)
    }
    
    if code ~= 204 then
        print("Failed to send message to Discord. Status code:", code)
        print("Response:", table.concat(response_body or {}))
    end
    
    -- Respect Discord rate limits
    os.execute("timeout /t " .. config.cooldown .. " /nobreak >nul")
end

-- Function to check if file contains keywords
local function fileContainsKeywords(filepath)
    local file = io.open(filepath, "r")
    if not file then return false end
    
    local content = file:read("*all")
    file:close()
    
    content = content:lower()
    for _, keyword in ipairs(config.keywords) do
        if content:find(keyword:lower(), 1, true) then
            return true
        end
    end
    
    return false
end

-- Function to get file size
local function getFileSize(filepath)
    local file = io.open(filepath, "r")
    if not file then return 0 end
    local size = file:seek("end")
    file:close()
    return size
end

-- Function to scan directory recursively
local function scanDirectory(directory)
    for entry in lfs.dir(directory) do
        if entry ~= "." and entry ~= ".." then
            local path = directory .. "\\" .. entry
            local attr = lfs.attributes(path)
            
            if attr.mode == "directory" then
                scanDirectory(path)  -- Recursively scan subdirectories
            else
                -- Check file extension
                local validExtension = false
                for _, ext in ipairs(config.fileExtensions) do
                    if entry:lower():sub(-#ext) == ext then
                        validExtension = true
                        break
                    end
                end
                
                -- Check file size
                local fileSize = getFileSize(path)
                if validExtension and fileSize > 0 and fileSize <= config.maxFileSize then
                    -- Check file content for keywords
                    if fileContainsKeywords(path) then
                        local message = string.format(
                            "⚠️ **Potential Brainrot Found**\n" ..
                            "📁 **File:** `%s`\n" ..
                            "📏 **Size:** %.2f KB\n" ..
                            "📂 **Path:** `%s`",
                            entry,
                            fileSize / 1024,
                            path
                        )
                        sendToDiscord(message)
                    end
                end
            end
        end
    end
end

-- Main function
local function main()
    print("Starting brainrot scanner...")
    sendToDiscord("🚀 Brainrot Scanner started! Beginning scan...")
    
    for _, path in ipairs(config.scanPaths) do
        if lfs.attributes(path, "mode") == "directory" then
            print("Scanning directory:", path)
            scanDirectory(path)
        else
            print("Directory not found:", path)
        end
    end
    
    sendToDiscord("✅ Brainrot scan completed!")
    print("Scan completed!")
end

-- Run the script
main()
