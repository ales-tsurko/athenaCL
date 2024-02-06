## Copying and Removing Texture Instances

TextureInstances can be duplicated with the command TIcp. The user is prompted to enter the name of the Texture to be copied, and then the name of the copy. The copy can be confirmed by listing all Textures with the command TIls.

**Copying a TextureInstance**

```
pi{auto-muteHiConga}ti{a1} :: ticp
which TextureInstnace to copy? (name or number 1-2): b1
name this copy of TI 'b1': b2
TextureInstance b2 created.

pi{auto-muteHiConga}ti{b2} :: tils
TextureInstances available:
{name,status,TM,PI,instrument,time,TC}
   a1               + LineGroove  auto-lowConga    64  00.0--20.0   0
   b1               + LineGroove  auto-muteHiConga 62  00.0--20.0   0
 + b2               + LineGroove  auto-muteHiConga 62  00.0--20.0   0
```

Textures can be deleted with the command TIrm, for TextureInstance Remove. The user is prompted to enter the name of the Texture to be deleted. The removal can be confirmed by listing all Textures with the command TIls.
      

**Removing a TextureInstance**

```
pi{auto-muteHiConga}ti{b2} :: tirm
which TextureInstnace to delete? (name or number 1-3): b2
are you sure you want to delete texture b2? (y, n, or cancel): y
TI b2 destroyed.

pi{auto-muteHiConga}ti{b1} :: tils
TextureInstances available:
{name,status,TM,PI,instrument,time,TC}
   a1               + LineGroove  auto-lowConga    64  00.0--20.0   0
 + b1               + LineGroove  auto-muteHiConga 62  00.0--20.0   0   

pi{auto-muteHiConga}ti{b1} :: 
```

When the active Texture is deleted, as it is above, athenaCL chooses a new Texture to activate, here choosing "b1." To select a different Texture, use the command TIo.
      
