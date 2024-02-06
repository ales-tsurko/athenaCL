## Introduction to Clones

A TextureClone (or a Clone or TC) is a musical part made from transformations of the exact events produced by a single Texture. Said another way, a Clone is not a copy of a Texture, but a transformed copy of the events produced by a Texture. Textures are not static entities, but algorithmic instructions that are "performed" each time an EventList is created. In order to capture and process the events of a single Texture, one or more Clones can be created in association with a single Texture.
      
Clones use Filter ParameterObjects to parametrically modify events produced from the parent Texture. Clones can be used to achieve a variety of musical structures. An echo is a simple example: by shifting the start time of events, a Clone can be used to create a time-shifted duplicate of a Texture's events. Clones can be used with a Texture to produce transformed motivic quotations of events, or can be used to thicken or harmonize a Texture with itself, for instance by filtering event pitch values.
      
Clones are also capable of non-parametric transformations that use CloneStatic ParameterObjects. For example a Clone, using a retrograde transformation, can reverse the events of a Texture.
      
