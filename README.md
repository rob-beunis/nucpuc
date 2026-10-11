# NuCPuC – formation of privileged PuC–NuC partner connections

Interactive simulation accompanying the article:

> Beunis R. (2021). Olivo-Cerebello-Nucleo-Olivary Loops Connectivity might be refined during the juvenile multi-innervation Phase of Climbing Fibers onto Purkinje Cells. Zenodo. https://doi.org/10.5281/zenodo.17575573

The program shows how Purkinje cell (PuC) axon terminals in the cerebellar nuclei can come to synapse heavily onto the nuclear cells (NuCs) that receive the same climbing fiber (CF), forming "privileged partner connections" (PPCs). This happens through hyperpolarization-rebound–triggered LTP and through LTD, even when the CF and PuC fiber tracts are scrambled. Every run takes a different random course.


## Live program

https://rob-beunis.github.io/nucpuc/

It runs in any modern web browser, with nothing to install. Each demo can be opened directly (page numbers are those printed at the bottom of the pages of the article):

- Demo 1 – Initial network (Fig. 1A, p. 4):
  https://rob-beunis.github.io/nucpuc/?demo=1
- Demo 2 – PuC axons scrambled (no figure):
  https://rob-beunis.github.io/nucpuc/?demo=2
- Demo 3 – CFs + PuC axons scrambled (Fig. 2A, p. 5):
  https://rob-beunis.github.io/nucpuc/?demo=3
- Demo 4 – One CF activated (Fig. 3, p. 5):
  https://rob-beunis.github.io/nucpuc/?demo=4
- Demo 5 – Partner formation, group size 1 (Fig. 4, p. 7):
  https://rob-beunis.github.io/nucpuc/?demo=5
- Demo 6 – Group size 10: LTP flooding, LTD clean-up (Fig. 5, p. 9):
  https://rob-beunis.github.io/nucpuc/?demo=6
- Demo 7 – CF hand over "one to many", juvenile multi-innervation (Fig. 6, p. 10):
  https://rob-beunis.github.io/nucpuc/?demo=7
- Demo 8 – Full program, all controls (no figure):
  https://rob-beunis.github.io/nucpuc/?demo=8
- Demo 9 – Failing run, LTP step 0.5 (Fig. 7, p. 11):
  https://rob-beunis.github.io/nucpuc/?demo=9

Optional additions to the address:

- `&speed=0.5` plays back at half speed. Values from 0.25 to 2 are accepted.
- `&seed=123` gives a reproducible run.

The playback speed can also be changed with the buttons below the demo panel.

The page counts anonymous visits and demo starts with GoatCounter (no cookies, no personal data).

Every button has an explanation (tooltip). With a mouse, rest the pointer on the button; on a tablet or phone, press and hold the button for about half a second. The program is easiest to use in landscape orientation on small screens.


## Contents of this repository

- `index.html`
  The web version (JavaScript, a single self-contained file). This is the live program.

- `python/nucpuc.py` (with `python/START_NUCPUC.bat`)
  The Python/Tkinter version. It requires Python 3 and Pillow (`pip install pillow`).
  Start it with `python nucpuc.py`, or with options: `--demo N`, `--speed 0.5`, `--seed N`, `--maximize`.

- `vfp/nucpuc.prg`
  The original Visual FoxPro 9.0 program (2019–2021), with its comments translated into English. The code itself is unchanged.

- `vfp/nucpuc_original_dutch_comments.prg`
  The same program with its original Dutch comments (converted to UTF-8 for display here).

The Python and web versions follow `nucpuc.prg` procedure by procedure, with the same procedure names, rules and parameters, and the same screen layout as the screenshots in the article. They differ from the original in a few deliberate ways:

- Random numbers: the random number generator differs from VFP's `RAND()`, so an individual VFP run cannot be reproduced exactly.
- Number comparisons: comparisons use a small tolerance, as VFP does.
- Wait loops: the empty `DOEVENTS` wait loops take the time measured in VFP 9.
- Text box: the text box in the right half of the original screen is omitted. The program never filled it; it only kept room free in the VFP environment in which the articles were embedded.
- Additions: a demo panel and a playback speed control were added.
- Interrupt buttons: they also work in the demos in which they are visible (demos 8 and 9), and the chosen interrupt is kept when switching to another demo. In the original, the demo mode never paused at a group size change. Clicking a red interrupt button again switches it off.
- Pause message: "Press any key to continue" blinks red on yellow, and a click (or tap) on the message also continues, which is convenient on tablets and phones.


## Acknowledgement

The original program was written by the author in Visual FoxPro 9.0. The translations into Python and into the web version were made with the assistance of Claude (Anthropic), an AI assistant, under the direction of the author, and were checked against the original program.


## Author

Rob Beunis, independent researcher (retired clinical neuropsychiatrist), Antwerp, Belgium.
ORCID: https://orcid.org/0009-0001-0529-2095


## License

MIT (see the file LICENSE). The article itself is licensed under CC BY 4.0.
