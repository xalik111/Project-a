function performLoginRequeust() {
    const login = document.querySelector('input#login').value;
    const password = document.querySelector('input#password').value;

    fetch('signup', {
        method: 'POST',
        body: JSON.stringify({
            l: 'bar'
        })
    }).then(response => response.json())
    .then(response => {
        document.querySelector('div.alert').innerHTML = response;
    });
}