-- Keep only the blocks that belong to the first level-1 section (release),
-- but drop the level-1 header itself.

local in_first_release = false
local past_first_release = false

return {
  {
    Header = function(h)
      if h.level == 1 then
        if not in_first_release and not past_first_release then
          -- Enter the first release; drop this H1 itself
          in_first_release = true
          return {}
        else
          -- Any subsequent H1 ends the first release; drop it and everything after
          past_first_release = true
          return {}
        end
      end
      -- For subheaders inside the first release, keep them; otherwise drop
      if past_first_release or not in_first_release then
        return {}
      end
      return h
    end,

    Block = function(b)
      -- Drop everything before the first H1 and after the next H1
      if past_first_release or not in_first_release then
        return {}
      end
      return b
    end,
  }
}