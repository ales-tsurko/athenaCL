# athenaCL

athenaCL is an algorithmic composition tool created by Christopher Ariza.

Or, as described by the author more specifically, it is a tool for:
> modular poly-paradigm algorithmic music composition in a cross-platform
> interactive command-line environment.




## Documentation

The manual is built using [mdBook](https://rust-lang.github.io/mdBook) you will
find the source code inside `doc/` directory. You can read it 
[here](https://alestsurko.by/athenaCL/).




## Tests

```
$ python3 -m unittest discover.athenaCL
$ python3 -m unittest discover athenaCL.libATH -p "*.py"
```




## About This Fork

The last commit in the original repo pushed in 2011. It was written in Python 2,
this repo updates the code to Python 3.

So far all tests of the main module (`libATH`) passed and it seems like it works
in the terminal.  But test coverage is far from 100% and many bugs introduced by
the conversion may still exist.

For now, I don't have any plans to introduce new features, but if you'll find
any bugs, I'm ready to try to fix them when I have time. So fill free to open
issues. Also, feel free to open PR's.

When I finish with the manual and fixing bugs I'll find in the examples of
tutorials, I'm going to keep it on "life support" - just fixing bugs, when I
find some while using the application as a normal user (i.e. not a tester).

I'd also like to add a front end to this application, but that would be a
separate project.
