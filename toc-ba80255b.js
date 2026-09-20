// Populate the sidebar
//
// This is a script, and not included directly in the page, to control the total size of the book.
// The TOC contains an entry for each page, so if each page includes a copy of the TOC,
// the total size of the page becomes O(n**2).
class MDBookSidebarScrollbox extends HTMLElement {
    constructor() {
        super();
    }
    connectedCallback() {
        this.innerHTML = '<ol class="chapter"><li class="chapter-item expanded "><li class="part-title">Getting Started</li></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="preface/02-overview-of-the-athenacl-system.html"><strong aria-hidden="true">1.</strong> Overview of the athenaCL System</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="preface/03-getting-started-and-advanced-work.html"><strong aria-hidden="true">2.</strong> Getting Started and Advanced Work</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="preface/04-more-information.html"><strong aria-hidden="true">3.</strong> More Information</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="preface/05-conventions-used-in-this-manual.html"><strong aria-hidden="true">4.</strong> Conventions Used in this Manual</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="preface/06-production-of-this-manual.html"><strong aria-hidden="true">5.</strong> Production of this Manual</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="getting-started.html"><strong aria-hidden="true">6.</strong> Installation</a></span></li><li class="chapter-item expanded "><li class="part-title">Tutorials</li></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter01/01-tutorial-1-the-interactive-command-line-interface.html"><strong aria-hidden="true">7.</strong> Tutorial 1: The Interactive Command Line Interface</a></span><ol class="section"><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter01/02-starting-the-athenacl-interpreter.html"><strong aria-hidden="true">7.1.</strong> Starting the athenaCL Interpreter</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter01/03-introduction-to-commands.html"><strong aria-hidden="true">7.2.</strong> Introduction to Command</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter01/04-viewing-command-names.html"><strong aria-hidden="true">7.3.</strong> Viewing Command Name</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter01/05-executing-commands.html"><strong aria-hidden="true">7.4.</strong> Executing Command</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter01/06-getting-help-for-commands.html"><strong aria-hidden="true">7.5.</strong> Getting Help for Command</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter01/07-configuring-the-user-environment.html"><strong aria-hidden="true">7.6.</strong> Configuring the User Environment</a></span></li></ol><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter02/01-tutorial-2-athenaobjects-and-eventmodes.html"><strong aria-hidden="true">8.</strong> Tutorial 2: AthenaObjects and EventModes</a></span><ol class="section"><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter02/02-introduction-to-athenaobjects.html"><strong aria-hidden="true">8.1.</strong> Introduction to AthenaObjects</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter02/03-loading-and-removing-an-athenaobject.html"><strong aria-hidden="true">8.2.</strong> Loading and Removing an AthenaObject</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter02/04-eventmodes-and-eventoutputs.html"><strong aria-hidden="true">8.3.</strong> EventModes and EventOutputs</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter02/05-creating-an-eventlist.html"><strong aria-hidden="true">8.4.</strong> Creating an EventList</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter02/06-configuring-and-using-csound.html"><strong aria-hidden="true">8.5.</strong> Configuring and Using Csound</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter02/07-saving-and-merging-athenaobjects.html"><strong aria-hidden="true">8.6.</strong> Saving and Merging AthenaObjects</a></span></li></ol><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter03/01-tutorial-3-creating-and-editing-paths.html"><strong aria-hidden="true">9.</strong> Tutorial 3: Creating and Editing Paths</a></span><ol class="section"><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter03/02-introduction-to-paths.html"><strong aria-hidden="true">9.1.</strong> Introduction to Paths</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter03/03-creating-selecting-and-viewing-pathinstances.html"><strong aria-hidden="true">9.2.</strong> Creating Selecting and Viewing PathInstances</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter03/04-copying-and-removing-pathinstances.html"><strong aria-hidden="true">9.3.</strong> Copying and Removing PathInstances</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter03/05-editing-pathinstances.html"><strong aria-hidden="true">9.4.</strong> Editing PathInstances</a></span></li></ol><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter04/01-tutorial-4-creating-and-editing-textures.html"><strong aria-hidden="true">10.</strong> Tutorial 4: Creating and Editing Textures</a></span><ol class="section"><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter04/02-introduction-to-textures-and-parameterobjects.html"><strong aria-hidden="true">10.1.</strong> Introduction to Textures and ParameterObjects</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter04/03-introduction-instrument-models.html"><strong aria-hidden="true">10.2.</strong> Introduction Instrument Models</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter04/04-selecting-and-viewing-texturemodules.html"><strong aria-hidden="true">10.3.</strong> Selecting and Viewing TextureModules</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter04/05-creating-selecting-and-viewing-textureinstances.html"><strong aria-hidden="true">10.4.</strong> Creating Selecting and Viewing TextureInstances</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter04/06-copying-and-removing-texture-instances.html"><strong aria-hidden="true">10.5.</strong> Copying and Removing Texture instances</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter04/07-editing-textureinstance-attributes.html"><strong aria-hidden="true">10.6.</strong> Editing TextureInstance Attributes</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter04/08-muting-textures.html"><strong aria-hidden="true">10.7.</strong> Muting Textures</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter04/09-viewing-and-searching-parameterobjects.html"><strong aria-hidden="true">10.8.</strong> Viewing and Searching ParameterObjects</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter04/010-editing-parameterobjects.html"><strong aria-hidden="true">10.9.</strong> Editing ParameterObjects</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter04/011-editing-rhythm-parameterobjects.html"><strong aria-hidden="true">10.10.</strong> Editing Rhythm ParameterObjects</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter04/012-editing-instruments-and-altering-eventmode.html"><strong aria-hidden="true">10.11.</strong> Editing Instruments and Altering EventMode</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter04/013-displaying-texture-parameter-values.html"><strong aria-hidden="true">10.12.</strong> Displaying Texture Parameter Values</a></span></li></ol><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter05/01-tutorial-5-textures-and-paths.html"><strong aria-hidden="true">11.</strong> Tutorial 5: Textures and Paths</a></span><ol class="section"><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter05/02-path-linking-and-pitch-formation-redundancy.html"><strong aria-hidden="true">11.1.</strong> Path Linking and Pitch Formation Redundancy</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter05/03-creating-a-path-with-a-duration-fraction.html"><strong aria-hidden="true">11.2.</strong> Creating a Path With a Duration Fraction</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter05/04-setting-eventmode-and-creating-a-texture.html"><strong aria-hidden="true">11.3.</strong> Setting EventMode and Creating a Texture</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter05/05-pitchmode.html"><strong aria-hidden="true">11.4.</strong> PitchMode</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter05/06-editing-local-octave.html"><strong aria-hidden="true">11.5.</strong> Editing Local Octave</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter05/07-editing-local-field-and-temperament.html"><strong aria-hidden="true">11.6.</strong> Editing Local Field and Temperament</a></span></li></ol><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter06/01-tutorial-6-textures-and-clones.html"><strong aria-hidden="true">12.</strong> Tutorial 6: Textures and Clones</a></span><ol class="section"><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter06/02-introduction-to-clones.html"><strong aria-hidden="true">12.1.</strong> Introduction to Clones</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter06/03-creating-and-editing-clones.html"><strong aria-hidden="true">12.2.</strong> Creating and Editing Clones</a></span></li></ol><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter07/01-tutorial-7-scripting-athenacl-in-python.html"><strong aria-hidden="true">13.</strong> Tutorial 7: Scripting athenaCL in Python</a></span><ol class="section"><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter07/02-creating-an-athenacl-interpreter-within-python.html"><strong aria-hidden="true">13.1.</strong> Creating an athenaCL Interpreter Within Python</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter07/03-creating-athenacl-generator-parameterobjects-within-python.html"><strong aria-hidden="true">13.2.</strong> Creating athenaCL Generator ParameterObjects Within Python</a></span></li><li class="chapter-item expanded "><span class="chapter-link-wrapper"><a href="chapter07/04-creating-athenacl-generator-parameterobjects-within-csound.html"><strong aria-hidden="true">13.3.</strong> Creating athenaCL Generator ParameterObjects Within Csound</a></span></li></ol></li></ol>';
        // Set the current, active page, and reveal it if it's hidden
        let current_page = document.location.href.toString().split('#')[0].split('?')[0];
        if (current_page.endsWith('/')) {
            current_page += 'index.html';
        }
        const links = Array.prototype.slice.call(this.querySelectorAll('a'));
        const l = links.length;
        for (let i = 0; i < l; ++i) {
            const link = links[i];
            const href = link.getAttribute('href');
            if (href && !href.startsWith('#') && !/^(?:[a-z+]+:)?\/\//.test(href)) {
                link.href = path_to_root + href;
            }
            // The 'index' page is supposed to alias the first chapter in the book.
            // Check both with and without the '.html' suffix to be robust against pretty URLs
            if (link.href.replace(/\.html$/, '') === current_page.replace(/\.html$/, '')
                || i === 0
                && path_to_root === ''
                && current_page.endsWith('/index.html')) {
                link.classList.add('active');
                let parent = link.parentElement;
                while (parent) {
                    if (parent.tagName === 'LI' && parent.classList.contains('chapter-item')) {
                        parent.classList.add('expanded');
                    }
                    parent = parent.parentElement;
                }
            }
        }
        // Track and set sidebar scroll position
        this.addEventListener('click', e => {
            if (e.target.tagName === 'A') {
                const clientRect = e.target.getBoundingClientRect();
                const sidebarRect = this.getBoundingClientRect();
                sessionStorage.setItem('sidebar-scroll-offset', clientRect.top - sidebarRect.top);
            }
        }, { passive: true });
        const sidebarScrollOffset = sessionStorage.getItem('sidebar-scroll-offset');
        sessionStorage.removeItem('sidebar-scroll-offset');
        if (sidebarScrollOffset !== null) {
            // preserve sidebar scroll position when navigating via links within sidebar
            const activeSection = this.querySelector('.active');
            if (activeSection) {
                const clientRect = activeSection.getBoundingClientRect();
                const sidebarRect = this.getBoundingClientRect();
                const currentOffset = clientRect.top - sidebarRect.top;
                this.scrollTop += currentOffset - parseFloat(sidebarScrollOffset);
            }
        } else {
            // scroll sidebar to current active section when navigating via
            // 'next/previous chapter' buttons
            const activeSection = document.querySelector('#mdbook-sidebar .active');
            if (activeSection) {
                activeSection.scrollIntoView({ block: 'center' });
            }
        }
        // Toggle buttons
        const sidebarAnchorToggles = document.querySelectorAll('.chapter-fold-toggle');
        function toggleSection(ev) {
            ev.currentTarget.parentElement.parentElement.classList.toggle('expanded');
        }
        Array.from(sidebarAnchorToggles).forEach(el => {
            el.addEventListener('click', toggleSection);
        });
    }
}
window.customElements.define('mdbook-sidebar-scrollbox', MDBookSidebarScrollbox);


// ---------------------------------------------------------------------------
// Support for dynamically adding headers to the sidebar.

(function() {
    // This is used to detect which direction the page has scrolled since the
    // last scroll event.
    let lastKnownScrollPosition = 0;
    // This is the threshold in px from the top of the screen where it will
    // consider a header the "current" header when scrolling down.
    const defaultDownThreshold = 150;
    // Same as defaultDownThreshold, except when scrolling up.
    const defaultUpThreshold = 300;
    // The threshold is a virtual horizontal line on the screen where it
    // considers the "current" header to be above the line. The threshold is
    // modified dynamically to handle headers that are near the bottom of the
    // screen, and to slightly offset the behavior when scrolling up vs down.
    let threshold = defaultDownThreshold;
    // This is used to disable updates while scrolling. This is needed when
    // clicking the header in the sidebar, which triggers a scroll event. It
    // is somewhat finicky to detect when the scroll has finished, so this
    // uses a relatively dumb system of disabling scroll updates for a short
    // time after the click.
    let disableScroll = false;
    // Array of header elements on the page.
    let headers;
    // Array of li elements that are initially collapsed headers in the sidebar.
    // I'm not sure why eslint seems to have a false positive here.
    // eslint-disable-next-line prefer-const
    let headerToggles = [];
    // This is a debugging tool for the threshold which you can enable in the console.
    let thresholdDebug = false;

    // Updates the threshold based on the scroll position.
    function updateThreshold() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;

        // The number of pixels below the viewport, at most documentHeight.
        // This is used to push the threshold down to the bottom of the page
        // as the user scrolls towards the bottom.
        const pixelsBelow = Math.max(0, documentHeight - (scrollTop + windowHeight));
        // The number of pixels above the viewport, at least defaultDownThreshold.
        // Similar to pixelsBelow, this is used to push the threshold back towards
        // the top when reaching the top of the page.
        const pixelsAbove = Math.max(0, defaultDownThreshold - scrollTop);
        // How much the threshold should be offset once it gets close to the
        // bottom of the page.
        const bottomAdd = Math.max(0, windowHeight - pixelsBelow - defaultDownThreshold);
        let adjustedBottomAdd = bottomAdd;

        // Adjusts bottomAdd for a small document. The calculation above
        // assumes the document is at least twice the windowheight in size. If
        // it is less than that, then bottomAdd needs to be shrunk
        // proportional to the difference in size.
        if (documentHeight < windowHeight * 2) {
            const maxPixelsBelow = documentHeight - windowHeight;
            const t = 1 - pixelsBelow / Math.max(1, maxPixelsBelow);
            const clamp = Math.max(0, Math.min(1, t));
            adjustedBottomAdd *= clamp;
        }

        let scrollingDown = true;
        if (scrollTop < lastKnownScrollPosition) {
            scrollingDown = false;
        }

        if (scrollingDown) {
            // When scrolling down, move the threshold up towards the default
            // downwards threshold position. If near the bottom of the page,
            // adjustedBottomAdd will offset the threshold towards the bottom
            // of the page.
            const amountScrolledDown = scrollTop - lastKnownScrollPosition;
            const adjustedDefault = defaultDownThreshold + adjustedBottomAdd;
            threshold = Math.max(adjustedDefault, threshold - amountScrolledDown);
        } else {
            // When scrolling up, move the threshold down towards the default
            // upwards threshold position. If near the bottom of the page,
            // quickly transition the threshold back up where it normally
            // belongs.
            const amountScrolledUp = lastKnownScrollPosition - scrollTop;
            const adjustedDefault = defaultUpThreshold - pixelsAbove
                + Math.max(0, adjustedBottomAdd - defaultDownThreshold);
            threshold = Math.min(adjustedDefault, threshold + amountScrolledUp);
        }

        if (documentHeight <= windowHeight) {
            threshold = 0;
        }

        if (thresholdDebug) {
            const id = 'mdbook-threshold-debug-data';
            let data = document.getElementById(id);
            if (data === null) {
                data = document.createElement('div');
                data.id = id;
                data.style.cssText = `
                    position: fixed;
                    top: 50px;
                    right: 10px;
                    background-color: 0xeeeeee;
                    z-index: 9999;
                    pointer-events: none;
                `;
                document.body.appendChild(data);
            }
            data.innerHTML = `
                <table>
                  <tr><td>documentHeight</td><td>${documentHeight.toFixed(1)}</td></tr>
                  <tr><td>windowHeight</td><td>${windowHeight.toFixed(1)}</td></tr>
                  <tr><td>scrollTop</td><td>${scrollTop.toFixed(1)}</td></tr>
                  <tr><td>pixelsAbove</td><td>${pixelsAbove.toFixed(1)}</td></tr>
                  <tr><td>pixelsBelow</td><td>${pixelsBelow.toFixed(1)}</td></tr>
                  <tr><td>bottomAdd</td><td>${bottomAdd.toFixed(1)}</td></tr>
                  <tr><td>adjustedBottomAdd</td><td>${adjustedBottomAdd.toFixed(1)}</td></tr>
                  <tr><td>scrollingDown</td><td>${scrollingDown}</td></tr>
                  <tr><td>threshold</td><td>${threshold.toFixed(1)}</td></tr>
                </table>
            `;
            drawDebugLine();
        }

        lastKnownScrollPosition = scrollTop;
    }

    function drawDebugLine() {
        if (!document.body) {
            return;
        }
        const id = 'mdbook-threshold-debug-line';
        const existingLine = document.getElementById(id);
        if (existingLine) {
            existingLine.remove();
        }
        const line = document.createElement('div');
        line.id = id;
        line.style.cssText = `
            position: fixed;
            top: ${threshold}px;
            left: 0;
            width: 100vw;
            height: 2px;
            background-color: red;
            z-index: 9999;
            pointer-events: none;
        `;
        document.body.appendChild(line);
    }

    function mdbookEnableThresholdDebug() {
        thresholdDebug = true;
        updateThreshold();
        drawDebugLine();
    }

    window.mdbookEnableThresholdDebug = mdbookEnableThresholdDebug;

    // Updates which headers in the sidebar should be expanded. If the current
    // header is inside a collapsed group, then it, and all its parents should
    // be expanded.
    function updateHeaderExpanded(currentA) {
        // Add expanded to all header-item li ancestors.
        let current = currentA.parentElement;
        while (current) {
            if (current.tagName === 'LI' && current.classList.contains('header-item')) {
                current.classList.add('expanded');
            }
            current = current.parentElement;
        }
    }

    // Updates which header is marked as the "current" header in the sidebar.
    // This is done with a virtual Y threshold, where headers at or below
    // that line will be considered the current one.
    function updateCurrentHeader() {
        if (!headers || !headers.length) {
            return;
        }

        // Reset the classes, which will be rebuilt below.
        const els = document.getElementsByClassName('current-header');
        for (const el of els) {
            el.classList.remove('current-header');
        }
        for (const toggle of headerToggles) {
            toggle.classList.remove('expanded');
        }

        // Find the last header that is above the threshold.
        let lastHeader = null;
        for (const header of headers) {
            const rect = header.getBoundingClientRect();
            if (rect.top <= threshold) {
                lastHeader = header;
            } else {
                break;
            }
        }
        if (lastHeader === null) {
            lastHeader = headers[0];
            const rect = lastHeader.getBoundingClientRect();
            const windowHeight = window.innerHeight;
            if (rect.top >= windowHeight) {
                return;
            }
        }

        // Get the anchor in the summary.
        const href = '#' + lastHeader.id;
        const a = [...document.querySelectorAll('.header-in-summary')]
            .find(element => element.getAttribute('href') === href);
        if (!a) {
            return;
        }

        a.classList.add('current-header');

        updateHeaderExpanded(a);
    }

    // Updates which header is "current" based on the threshold line.
    function reloadCurrentHeader() {
        if (disableScroll) {
            return;
        }
        updateThreshold();
        updateCurrentHeader();
    }


    // When clicking on a header in the sidebar, this adjusts the threshold so
    // that it is located next to the header. This is so that header becomes
    // "current".
    function headerThresholdClick(event) {
        // See disableScroll description why this is done.
        disableScroll = true;
        setTimeout(() => {
            disableScroll = false;
        }, 100);
        // requestAnimationFrame is used to delay the update of the "current"
        // header until after the scroll is done, and the header is in the new
        // position.
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                // Closest is needed because if it has child elements like <code>.
                const a = event.target.closest('a');
                const href = a.getAttribute('href');
                const targetId = href.substring(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    threshold = targetElement.getBoundingClientRect().bottom;
                    updateCurrentHeader();
                }
            });
        });
    }

    // Takes the nodes from the given head and copies them over to the
    // destination, along with some filtering.
    function filterHeader(source, dest) {
        const clone = source.cloneNode(true);
        clone.querySelectorAll('mark').forEach(mark => {
            mark.replaceWith(...mark.childNodes);
        });
        dest.append(...clone.childNodes);
    }

    // Scans page for headers and adds them to the sidebar.
    document.addEventListener('DOMContentLoaded', function() {
        const activeSection = document.querySelector('#mdbook-sidebar .active');
        if (activeSection === null) {
            return;
        }

        const main = document.getElementsByTagName('main')[0];
        headers = Array.from(main.querySelectorAll('h2, h3, h4, h5, h6'))
            .filter(h => h.id !== '' && h.children.length && h.children[0].tagName === 'A');

        if (headers.length === 0) {
            return;
        }

        // Build a tree of headers in the sidebar.

        const stack = [];

        const firstLevel = parseInt(headers[0].tagName.charAt(1));
        for (let i = 1; i < firstLevel; i++) {
            const ol = document.createElement('ol');
            ol.classList.add('section');
            if (stack.length > 0) {
                stack[stack.length - 1].ol.appendChild(ol);
            }
            stack.push({level: i + 1, ol: ol});
        }

        // The level where it will start folding deeply nested headers.
        const foldLevel = 3;

        for (let i = 0; i < headers.length; i++) {
            const header = headers[i];
            const level = parseInt(header.tagName.charAt(1));

            const currentLevel = stack[stack.length - 1].level;
            if (level > currentLevel) {
                // Begin nesting to this level.
                for (let nextLevel = currentLevel + 1; nextLevel <= level; nextLevel++) {
                    const ol = document.createElement('ol');
                    ol.classList.add('section');
                    const last = stack[stack.length - 1];
                    const lastChild = last.ol.lastChild;
                    // Handle the case where jumping more than one nesting
                    // level, which doesn't have a list item to place this new
                    // list inside of.
                    if (lastChild) {
                        lastChild.appendChild(ol);
                    } else {
                        last.ol.appendChild(ol);
                    }
                    stack.push({level: nextLevel, ol: ol});
                }
            } else if (level < currentLevel) {
                while (stack.length > 1 && stack[stack.length - 1].level > level) {
                    stack.pop();
                }
            }

            const li = document.createElement('li');
            li.classList.add('header-item');
            li.classList.add('expanded');
            if (level < foldLevel) {
                li.classList.add('expanded');
            }
            const span = document.createElement('span');
            span.classList.add('chapter-link-wrapper');
            const a = document.createElement('a');
            span.appendChild(a);
            a.href = '#' + header.id;
            a.classList.add('header-in-summary');
            filterHeader(header.children[0], a);
            a.addEventListener('click', headerThresholdClick);
            const nextHeader = headers[i + 1];
            if (nextHeader !== undefined) {
                const nextLevel = parseInt(nextHeader.tagName.charAt(1));
                if (nextLevel > level && level >= foldLevel) {
                    const toggle = document.createElement('a');
                    toggle.classList.add('chapter-fold-toggle');
                    toggle.classList.add('header-toggle');
                    toggle.addEventListener('click', () => {
                        li.classList.toggle('expanded');
                    });
                    const toggleDiv = document.createElement('div');
                    toggleDiv.textContent = '❱';
                    toggle.appendChild(toggleDiv);
                    span.appendChild(toggle);
                    headerToggles.push(li);
                }
            }
            li.appendChild(span);

            const currentParent = stack[stack.length - 1];
            currentParent.ol.appendChild(li);
        }

        const onThisPage = document.createElement('div');
        onThisPage.classList.add('on-this-page');
        onThisPage.append(stack[0].ol);
        const activeItemSpan = activeSection.parentElement;
        activeItemSpan.after(onThisPage);
    });

    document.addEventListener('DOMContentLoaded', reloadCurrentHeader);
    document.addEventListener('scroll', reloadCurrentHeader, { passive: true });
})();

