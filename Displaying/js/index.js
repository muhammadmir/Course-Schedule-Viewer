function formatProp(properties) {
    str = ''
    for (var i = 0; i < properties.length; i++) {
        str += '<table class="format-properties-table" border="1" width="100%">'

        str += '<thead class="meeting-time">'
        str += '<tr>'
        str += '<td colspan=7 style="text-align: center;">Schedule Meeting Times #' + (i + 1).toString() + '</td>'
        str += '</tr>'
        str += '</thead>'

        str += '<thead class="meeting-properties-head">'
        str += '<tr>'
        str += '<td style="font-weight:bold">Type</td>'
        str += '<td style="font-weight:bold">Nature</td>'
        str += '<td style="font-weight:bold">Time</td>'
        str += '<td style="font-weight:bold">Days</td>'
        str += '<td style="font-weight:bold">Location</td>'
        str += '<td style="font-weight:bold">Period</td>'
        str += '<td style="font-weight:bold">Instructors</td>'
        str += '</tr>'
        str += '</thead>'


        str += '<tbody class="meeting-properties-body">'
        str += '<td>' + properties[i].Type + '</td>'
        str += '<td>' + properties[i].Nature + '</td>'
        str += '<td>' + properties[i].Time + '</td>'
        str += '<td>' + properties[i].Days.join(', ') + '</td>'
        str += '<td>' + properties[i].Location + '</td>'
        str += '<td>' + properties[i].Period + '</td>'
        str += '<td>' + properties[i].Instructors.join(', ') + '</td>'
        str += '</tr>'
        str += '</tbody>'

        str += '</table>'
    }
    return str
}

function formatCRN(crn) {
    if (crn != null) return '<tr><td colspan="7"><b>CRN: </b>' + crn + '</td></tr>';
    else return '';
}

function formatDesc(description) {
    if (description != null) return '<tr><td colspan="7"><b>Description: </b>' + description + '</td></tr>';
    else return ''
}

function formatAttr(attributes) {
    if (attributes != null) return '<tr><td colspan="7"><b>Attributes: </b>' + attributes.join(", ") + '</td></tr>';
    else return ''
}

function formatPreReq(prerequisites) {
    if (prerequisites != null) return '<tr><td colspan="7"><b>Prerequisites: </b>' + prerequisites.join(", ") + '</td></tr>';
    else return ''
}

function formatCoReq(corequisites) {
    if (corequisites != null) return '<tr><td colspan="7"><b>Corequisites: </b>' + corequisites.join(", ") + '</td></tr>';
    else return ''
}

function formatMutualExclusions(mutualExclusions) {
    if (mutualExclusions != null) return '<tr><td colspan="7"><b>Mutual Exclusions: </b>' + mutualExclusions.join(", ") + '</td></tr>';
    else return ''
}

function formatCrossList(crossListCourses) {
    if (crossListCourses != null) return '<tr><td colspan="7"><b>Cross List Courses: </b>' + crossListCourses.join(", ") + '</td></tr>';
    else return ''
}

function formatRestrictions(restrictions) {
    if (restrictions != null) {

        let entry = '';

        restrictions.forEach(item => {
            const description = `<br><b>${item.Description}</b>`;

            let reqList = '';
            item.Requirements.forEach(requirement => {
                reqList += `<li>${requirement}</li>`;
            });

            entry += `${description}<ul>${reqList}</ul>`;
        });

        return '<tr><td colspan="7"><b>Restrictions: </b>' + entry + '</td></tr>';
    }
    else return ''
}

/* Formatting function for row details - modify as you need */
function format(course) {
    return (
        '<table class="format-table">' +
        formatCRN(course.CRN) +
        formatDesc(course.Description) +
        formatPreReq(course.Prerequisites) +
        formatCoReq(course.Corequisites) +
        formatMutualExclusions(course["Mutual Exclusions"]) +
        formatCrossList(course["Cross List Courses"]) +
        formatRestrictions(course["Restrictions"]) +
        formatAttr(course.Attributes) +
        formatProp(course.Properties) +
        '</table>'
    );
}

function createTable(flattenedCalendarArray) {
    try {
        return $('#courses').DataTable({
            data: flattenedCalendarArray,
            dom: 'Pfrltip',
            lengthMenu: [10, 25, 50, 75, 100],
            searchPanes: {
                cascadePanes: true,
                threshold: 1.0,
                layout: 'columns-4'
            },
            columnDefs: [
                {
                    visible: false,
                    targets: [1, 7, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
                },
                {
                    searchPanes: {
                        show: false
                    },
                    targets: [1, 2, 4, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 23]
                },
                {
                    searchPanes: {
                        show: true,
                        combiner: sessionStorage['Pane Logic'].toLowerCase()
                    },
                    targets: [3, 18, 19, 20, 21, 22, 24, 25, 26]
                },
                { // Filter by course level
                    searchPanes: {
                        options: [
                            {
                                label: "000-199",
                                value: function (rowData, rowIdx) {
                                    let courseLevel = parseInt(rowData.Level);
                                    return courseLevel <= 199;
                                }
                            },
                            {
                                label: "200-299",
                                value: function (rowData, rowIdx) {
                                    let courseLevel = parseInt(rowData.Level);
                                    return courseLevel >= 200 && courseLevel <= 299;
                                }
                            },
                            {
                                label: "300-499",
                                value: function (rowData, rowIdx) {
                                    let courseLevel = parseInt(rowData.Level);
                                    return courseLevel >= 300 && courseLevel <= 499;
                                }
                            },
                            {
                                label: "500-999",
                                value: function (rowData, rowIdx) {
                                    let courseLevel = parseInt(rowData.Level);
                                    return courseLevel >= 500 && courseLevel <= 999;
                                }
                            },
                            {
                                label: "1000+",
                                value: function (rowData, rowIdx) {
                                    let courseLevel = parseInt(rowData.Level);
                                    return courseLevel >= 1000;
                                }
                            }
                        ],
                        combiner: sessionStorage['Pane Logic'].toLowerCase()
                    },
                    targets: [5]
                },
                { // Filter by capacity: Available, Full, Waitlisted
                    searchPanes: {
                        options: [
                            {
                                label: 'Available',
                                value: function (rowData, rowIdx) {
                                    return rowData.Remaining > 0;
                                }
                            },
                            {
                                label: 'Full',
                                value: function (rowData, rowIdx) {
                                    return rowData.Remaining <= 0 && rowData.Waitlisted <= 0;
                                }
                            },
                            {
                                label: 'Waitlisted',
                                value: function (rowData, rowIdx) {
                                    return rowData.Waitlisted > 0;
                                }
                            }
                        ],
                        combiner: sessionStorage['Pane Logic'].toLowerCase()
                    },
                    targets: [9]
                }
            ],
            columns: [
                { // 0
                    className: 'dt-control',
                    orderable: true,
                    data: null,
                    defaultContent: '',
                },
                { data: 'CRN' },
                { data: 'Section' }, // 2
                { data: 'Subject' },
                { data: 'Abbreviation' }, // 4
                { data: 'Level' },
                { data: 'Name' }, // 6
                { data: 'Description' },
                { data: 'Credits' }, // 8
                { data: 'Capacity' },
                { data: 'Registered' }, // 10
                { data: 'Remaining' },
                { data: 'Waitlisted' }, // 12
                { data: 'Prerequisites' },
                { data: 'Corequisites' }, // 14
                { data: 'Mutual Exclusions' },
                { data: 'Cross List Courses' }, // 16
                { data: 'Restrictions' },
                { data: 'Attributes', render: { sp: '[]' }, searchPanes: { header: 'Attribute', orthogonal: 'sp' } }, // 18
                { data: 'Properties.0.Type', searchPanes: { header: 'Type' } },
                { data: 'Properties.0.Time', searchPanes: { header: 'Time' } }, // 20
                { data: 'Properties.0.Days', render: { sp: '[]' }, searchPanes: { header: 'Day', orthogonal: 'sp' } },
                { data: 'Properties.0.Location', searchPanes: { header: 'Location' } }, // 22
                { data: 'Properties.0.Period' },
                { data: 'Properties.0.Nature', searchPanes: { header: 'Nature' } }, // 24
                { data: 'Properties.0.Instructors', render: { sp: '[]' }, searchPanes: { header: 'Instructor', orthogonal: 'sp' } },
                { data: 'Calendar Name', searchPanes: { show: true, header: 'Calendar' } } // 26
            ],
        });
    } catch (error) {
        console.error('Error occured when creating table:', error);
    }
    return null;
}

// https://stackoverflow.com/a/65939108
const saveFileAsJson = (filename, dataObjToWrite) => {
    const blob = new Blob([JSON.stringify(dataObjToWrite)], { type: "text/json" });
    const link = document.createElement("a");

    link.download = filename;
    link.href = window.URL.createObjectURL(blob);
    link.dataset.downloadurl = ["text/json", link.download, link.href].join(":");

    const evt = new MouseEvent("click", {
        view: window,
        bubbles: true,
        cancelable: true,
    });

    link.dispatchEvent(evt);
    link.remove()
};

function detectDevice() {
    const platform = navigator.platform.toLowerCase();
    const isMac = platform.includes('mac');
    const isWindows = platform.includes('win');

    if (isMac) return "Mac"
    if (isWindows) return "Windows"
    return "Neither"
}

$(document).ready(function () {
    let flattenedCalendarArray = [];

    function showElement(elementID) {
        const element = document.getElementById(elementID);
        element ? element.classList.remove('d-none') : console.error(`Element with ID ${id} not found.`);
    }

    function hideElement(elementID) {
        const element = document.getElementById(elementID);
        element ? element.classList.add('d-none') : console.error(`Element with ID ${id} not found.`);
    }

    // Initially hide Table Panel and Alert
    hideElement('panel');
    hideElement('alert');

    document.getElementById('formFile').addEventListener('change', (event) => {
        try {
            let file = event.target.files[0];
            var fr = new FileReader();

            fr.onload = function (e) {
                try {
                    let calendarObj = JSON.parse(e.target.result);

                    // De-flatttening (or de-normalizing?) so that Calendar Name is property of each Course object
                    // This will allow more simple integration of a SearchPane allowing to filter by specific Calendar(s)
                    calendarObj.forEach(calendar => {
                        calendar.Courses.forEach(course => {
                            course["Calendar Name"] = calendar["Calendar Name"];
                            flattenedCalendarArray.push(course);
                        });
                    });

                    hideElement('fileLoading');
                    showElement('panel');
                    document.title = 'Course View Panel';
                } catch (error) {
                    showElement('alert');
                    console.log(error);
                }
            };

            fr.readAsText(file);
        } catch (error) {
            showElement('alert');
            console.log(error);
        }
    });


    // Main function
    function loadCoursePanel() {
        // Displaying Pane Logic
        sessionStorage['Pane Logic'] = sessionStorage['Pane Logic'] == undefined ? 'OR' : sessionStorage['Pane Logic'];
        document.getElementById('paneLogic').textContent = 'Inter-Pane Logic: ' + sessionStorage['Pane Logic'];

        // Displaying Keyboard Tip
        let device = detectDevice();
        let keyboardTipPrefix = 'Tip: To select multiple Options in one or more Search Panes, press ';
        keyboardTipPrefix += device == 'Mac' ? '<kbd>⌘</kbd> + Click' : '<kbd>Ctrl</kbd> + Click';
        keyboardTipPrefix = device == 'Neither' ? 'Tip: View this page on a computer!' : keyboardTipPrefix;
        document.getElementById('keyboardTip').innerHTML = keyboardTipPrefix;

        let table = createTable(flattenedCalendarArray);

        // Add event listener for opening and closing details
        $('#courses tbody').on('click', 'td.dt-control', function () {
            var tr = $(this).closest('tr');
            var row = table.row(tr);

            if (row.child.isShown()) {
                // This row is already open - close it
                row.child.hide();
                tr.removeClass('shown');
            } else {
                // Open this row
                row.child(format(row.data())).show();
                tr.addClass('shown');
            }
        });

        // Pane Logic Changes
        document.getElementById('paneLogic').addEventListener('click', () => {
            sessionStorage['Pane Logic'] = sessionStorage['Pane Logic'] == 'OR' ? 'AND' : 'OR';
            document.getElementById('paneLogic').textContent = 'Inter-Pane Logic: ' + sessionStorage['Pane Logic'];
            location.reload();
        });

        // Downloading
        document.getElementById('downloadSelectedRows').addEventListener('click', () => {
            let data = Array.from(table.rows({ search: 'applied' }).data());
            saveFileAsJson('Filtered.json', data);
        });
    }

    // Create a MutationObserver to watch for changes
    const observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            if (mutation.attributeName === "class") {
                const element = mutation.target;
                if ($(element).hasClass('d-none')) {
                    loadCoursePanel();
                }
            }
        });
    });

    // Start observing the target element for configured mutations
    const targetNode = document.getElementById('fileLoading');
    observer.observe(targetNode, { attributes: true });
});
