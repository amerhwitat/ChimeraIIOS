-- mpv OSD for the system-installed Init.mp4 splash.
-- Progress is event-driven: this overlay never advances the percent itself.
local mp = require 'mp'
local state_path = os.getenv('CHIMERA_PROGRESS_FILE') or '/run/chimera/koronos-progress.state'

local function read_state()
    local f = io.open(state_path, 'r')
    if not f then
        return {percent=-1, phase='Starting Chimera II OS', message='Waiting for initialization events'}
    end
    local values = {}
    for line in f:lines() do
        local k, v = line:match('^([%w_]+)=(.*)$')
        if k then values[k] = v end
    end
    f:close()
    local p = tonumber(values.percent or '-1') or -1
    p = math.max(-1, math.min(100, p))
    local phase = values.phase or 'Initializing'
    local message = values.message or 'Waiting for the next boot event'
    -- Also support the Aurora percent|phase|message writer.
    if p < 0 then
        local sf = io.open(state_path, 'r')
        if sf then
            local line = sf:read('*l') or ''
            sf:close()
            local n, ph, msg = line:match('^(%d+)|([^|]*)|(.*)$')
            if n then p, phase, message = tonumber(n), ph, msg end
        end
    end
    return {percent=p, phase=phase, message=message}
end

local function render()
    local s = read_state()
    local width = 42
    local p = math.max(0, s.percent)
    local filled = math.floor(width * p / 100)
    local bar = string.rep('━', filled) .. string.rep('─', width - filled)
    local percent = s.percent < 0 and ' --%' or string.format('%3d%%', s.percent)
    local overlay = string.format(
        '{\\an2\\fs25\\bord2\\shad1\\1c&HFFFFFF&\\3c&H30200A&}' ..
        'CHIMERA II OS  |  %s\\N%s %s\\N%s',
        s.phase, bar, percent, s.message)
    mp.set_osd_ass(0, 0, overlay)
end

mp.add_periodic_timer(0.25, render)
render()
