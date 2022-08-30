const songListUl = document.getElementById("song-list");
songListWrapper = document.getElementById("song-list-wrapper");

window.addEventListener("DOMContentLoaded", loadWait(populateSongList));
setInterval(populateSongList, 10000);

// In order to prevent flickering, disable entire body until promise is complete
async function loadWait(promiseCallback) {
  document.body.style.display = "none";
  await promiseCallback();
  document.body.style.display = "block";
}


async function get_current_user() {
    const response = await fetch("/get_current_user");
    const data = await response.json();
    return data;
}


async function populateSongList() {
    const response = await fetch("get_current_songs");
    const data = await response.json();
    const current_user = await get_current_user();

    if (data.length === 0) {
        window.location.replace("/add_song");
    }
    
    const lis = data.map((song) => {
    const li = document.createElement("li");
    li.innerHTML = `
                <div class="song-wrapper">
                    <p class="song-name">${song.song_name}${
        song.singer.id != current_user.id ? ` (Added by ${song.singer.first_name} ${song.singer.last_name})` : ""
    }</p>
                    ${
                        song.singer.id === current_user.id
                        ? `<i class="fa-solid fa-xmark delete-song" id=${song.id}></i>`
                        : ""
                    }
                </div>`;


    if (song.duet_partner && song.singer.id == current_user.id) {
        li.innerHTML += `
                <div class="other-singers">
                    <p>Together with: ${song.duet_partner.first_name} ${song.duet_partner.last_name}</p>
                </div>`;
    }
    return li;
    });
    songListUl.replaceChildren(...lis);
    setDeletelinks();
}


function setDeletelinks() {
  const deleteSongLinks = document.querySelectorAll(".delete-song");
  deleteSongLinks.forEach((link) => {
    link.addEventListener("click", async (e) => {
      e.preventDefault();

      const songPK = e.currentTarget.id;
      const response = await fetch(`/get_song/${songPK}`);
      const data = await response.json();

      if (!response.ok) {
        alert(`Error: ${data.error}`);
        return;
      }

      if (confirm(`Are you sure you want to remove ${data.name}?`)) {
        fetch(`/delete_song/${songPK}`)
          .then(() => populateSongList())
          .catch((error) => console.error(error));
      }
    });
  });
}

