-- Strip everything after the first section
-- (i.e. the notes for the last release).

release_count = 0

return {
  {
    Header = function (elem)
      if elem.level == 2 then
        release_count = release_count + 1
      end
      if elem.level < 3 or release_count > 1 then
        return pandoc.Null()
      end
      return elem
    end,
    Block = function (elem)
      if release_count > 1 then
        return pandoc.Null()
      end
      return elem
    end,
  }
}
