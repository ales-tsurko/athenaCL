## Displaying Texture Parameter Values

It is often useful to view the values produced by a Texture with a graphical diagram. The command TImap provides a multi-parameter display of all raw values input from ParameterObjects into the Texture. The values displayed by TImap are pre-TextureModule, meaning that they are the raw values produced by the ParameterObjects; the final parametric event values may be altered or completely changed by the Texture's internal processing (its TextureModule) to produce different arrangements of events. The TImap command thus only provides a partial representation of what a Texture produces.
      
To view a TImap display, the user's graphic preferences must be properly set (see  for more information). The command TImap displays the active Texture:
      

**Viewing a Texture with TImap**

```
pi{auto-muteHiConga}ti{b1} :: timap
TImap (event-base, pre-TM) display complete.
```

