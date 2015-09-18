/** @file */
#include "client-model.h"

/**
 * Removes all changes which are still stored.
 */
void ClientModel::flush_changes()
{
    change_ptr change;
    while ((change = get_next_change()) != 0)
        delete change;
}

/**
 * Checks if the change queue is empty.
 *
 * @return True if no changes remain, False otherwise.
 */
bool ClientModel::has_more_changes()
{
    return !m_changes.empty();
}

/**
 * Gets the next change, or NULL if no changes remain.
 *
 * Note that this change should be deleted after the caller is finished with
 * it.
 */
ClientModel::change_ptr ClientModel::get_next_change()
{
    if (has_more_changes())
    {
        change_ptr change = m_changes.front();
        m_changes.pop();
        return change;
    }
    else
        return 0;
}

/**
 * Returns whether or not a client exists.
 */
bool ClientModel::is_client(Window client)
{
    return m_desktops.is_member(client);
}

/**
 * Returns whether or not a client is visible.
 */
bool ClientModel::is_visible(Window client)
{
    desktop_ptr desktop_of = m_desktops.get_category_of(client);
    if (desktop_of->is_all_desktop())
        return true;

    if (desktop_of->is_user_desktop())
        return *desktop_of == *m_current_desktop;

    return false;
}

/**
 * Returns whether a particular desktop as a whole is visible.
 */
bool ClientModel::is_visible_desktop(desktop_ptr desktop)
{
    if (desktop->is_all_desktop())
        return true;

    if (desktop->is_user_desktop())
        return *desktop == *m_current_desktop;

    return false;
}

/**
 * Gets a list of all of the clients on a desktop.
 */
void ClientModel::get_clients_of(desktop_ptr desktop,
    std::vector<Window> &return_clients)
{
    for (client_iter iter = m_desktops.get_members_of_begin(desktop);
            iter != m_desktops.get_members_of_end(desktop);
            iter++)
        return_clients.push_back(*iter);
}

/**
 * Gets a list of all of the visible clients.
 */
void ClientModel::get_visible_clients(std::vector<Window> &return_clients)
{
    for (client_iter iter = 
                m_desktops.get_members_of_begin(m_current_desktop);
            iter != m_desktops.get_members_of_end(m_current_desktop);
            iter++)
        return_clients.push_back(*iter);

    for (client_iter iter = 
                m_desktops.get_members_of_begin(ALL_DESKTOPS);
            iter != m_desktops.get_members_of_end(ALL_DESKTOPS);
            iter++)
        return_clients.push_back(*iter);
}

/**
 * Gets all of the visible windows, but sorted by layer from bottom to
 * top.
 */
void ClientModel::get_visible_in_layer_order(std::vector<Window> &return_clients)
{
    get_visible_clients(return_clients);

    UniqueMultimapSorter<Layer, Window> layer_sorter(m_layers);
    std::sort(return_clients.begin(), return_clients.end(),
            layer_sorter);
}

/**
 * Adds a new client with some basic initial state.
 */
void ClientModel::add_client(Window client, InitialState state,
    Dimension2D location, Dimension2D size)
{
    if (DIM2D_WIDTH(size) <= 0 || DIM2D_HEIGHT(size) <= 0)
        return;

    // Special care is given to honor the initial state, since it is
    // mandated by the ICCCM
    switch (state)
    {
        case IS_VISIBLE:
            m_desktops.add_member(m_current_desktop, client);
            push_change(new ChangeClientDesktop(client, 0,
                        m_current_desktop));
            break;
        case IS_HIDDEN:
            m_desktops.add_member(ICON_DESKTOP, client);
            push_change(new ChangeClientDesktop(client, 0, ICON_DESKTOP));
            break;
    }

    m_layers.add_member(DEF_LAYER, client);
    push_change(new ChangeLayer(client, DEF_LAYER));

    // Since the size and locations are already current, don't put out
    // an event now that they're set
    m_location[client] = location;
    m_size[client] = size;

    focus(client);
}

/**
 * Removes a client.
 *
 * Note that this method will put out a ChangeFocus event, but that event will
 * have a nonexistent 'prev_focus' field (pointing to the client that is
 * destroyed). Other than that event, however, no other notification will be
 * delivered that this window was removed.
 */
void ClientModel::remove_client(Window client)
{
    if (!is_client(client))
        return;

    // A destroyed window cannot be focused.
    unfocus_if_focused(client);

    // Unregister the client from any categories it may be a member of, but
    // keep a copy of each of the categories so we can pass it on to notify
    // that the window was destroyed (don't copy the size/location though,
    // since they will most likely be invalid, and of no use anyway)
    const Desktop *desktop = find_desktop(client);
    Layer layer = find_layer(client);

    m_desktops.remove_member(client);
    m_layers.remove_member(client);
    m_location.erase(client);
    m_size.erase(client);

    push_change(new DestroyChange(client, desktop, layer));
}

/**
 * Changes the location of a client.
 */
void ClientModel::change_location(Window client, Dimension x, Dimension y)
{
    m_location[client] = Dimension2D(x, y);
    push_change(new ChangeLocation(client, x, y));
}

/**
 * Changes the size of a client.
 */
void ClientModel::change_size(Window client, Dimension width, Dimension height)
{
    if (width > 0 && height > 0)
    {
        m_size[client] = Dimension2D(width, height);
        push_change(new ChangeSize(client, width, height));
    }
}

/**
 * Gets the currently focused window.
 */
Window ClientModel::get_focused()
{
    return m_focused;
}

/**
 * Changes the focus to another window. Note that this fails if the client
 * is not currently visible.
 */
void ClientModel::focus(Window client)
{
    if (!is_visible(client))
        return;

    Window old_focus = m_focused;
    m_focused = client;
    push_change(new ChangeFocus(old_focus, client));
}

/**
 * Unfocuses a window if it is currently focused.
 */
void ClientModel::unfocus()
{
    if (m_focused != None)
    {
        Window old_focus = m_focused;
        m_focused = None;
        push_change(new ChangeFocus(old_focus, None));
    }
}

/**
 * Unfocuses a window if it is currently focused, otherwise the focus is
 * not changed.
 */
void ClientModel::unfocus_if_focused(Window client)
{
    if (m_focused == client)
        unfocus();
}

/**
 * Gets the current desktop which the client inhabits.
 *
 * You should _NEVER_ free the value returned by this function.
 */
ClientModel::desktop_ptr ClientModel::find_desktop(Window client)
{
    if (m_desktops.is_member(client))
        return m_desktops.get_category_of(client);
    else
        return static_cast<ClientModel::desktop_ptr>(0);
}

/**
 * Gets the current layer which the client inhabits.
 */
Layer ClientModel::find_layer(Window client)
{
    if (m_desktops.is_member(client))
        return m_layers.get_category_of(client);
    else
        return INVALID_LAYER;
}

/**
 * Moves a client up in the layer stack.
 */
void ClientModel::up_layer(Window client)
{
    Layer old_layer = m_layers.get_category_of(client);
    if (old_layer < MAX_LAYER)
    {
        m_layers.move_member(client, old_layer + 1);
        push_change(new ChangeLayer(client, old_layer + 1));
    }
}

/**
 * Moves a client up in the layer stack.
 */
void ClientModel::down_layer(Window client)
{
    Layer old_layer = m_layers.get_category_of(client);
    if (old_layer > MIN_LAYER)
    {
        m_layers.move_member(client, old_layer - 1);
        push_change(new ChangeLayer(client, old_layer - 1));
    }
}

/**
 * Changes the layer of a client.
 */
void ClientModel::set_layer(Window client, Layer layer)
{
    if (!m_layers.is_category(layer))
        return;

    Layer old_layer = m_layers.get_category_of(client);
    if (old_layer != layer)
    {
        m_layers.move_member(client, layer);
        push_change(new ChangeLayer(client, layer));
    }
}

/**
 * Toggles the stickiness of a client.
 */
void ClientModel::toggle_stick(Window client)
{
    if (!is_visible(client))
        return;

    desktop_ptr old_desktop = m_desktops.get_category_of(client);
    if (old_desktop->is_user_desktop())
        move_to_desktop(client, ALL_DESKTOPS, false);
    else
        move_to_desktop(client, m_current_desktop, true);
}

/**
 * Moves a client onto the current desktop.
 *
 * Note that this will not work if the client is on:
 *  - The "all" desktop
 *  - The "moving/resizing" desktops
 *  - The "icon" desktop
 */
void ClientModel::client_reset_desktop(Window client)
{
    desktop_ptr old_desktop = m_desktops.get_category_of(client);
    if (!old_desktop->is_user_desktop())
        return;

    move_to_desktop(client, m_current_desktop, false);
}

/**
 * Moves a client onto the next desktop.
 */
void ClientModel::client_next_desktop(Window client)
{
    desktop_ptr old_desktop = m_desktops.get_category_of(client);
    if (!old_desktop->is_user_desktop())
        return;

    user_desktop_ptr user_desktop = 
        dynamic_cast<user_desktop_ptr>(old_desktop);
    unsigned long long desktop_index = user_desktop->desktop;
    desktop_index  = (desktop_index + 1) % m_max_desktops;
    move_to_desktop(client, USER_DESKTOPS[desktop_index], true);
}

/**
 * Moves a client onto the previous desktop.
 */
void ClientModel::client_prev_desktop(Window client)
{
    desktop_ptr old_desktop = m_desktops.get_category_of(client);
    if (!old_desktop->is_user_desktop())
        return;

    user_desktop_ptr user_desktop = 
        dynamic_cast<user_desktop_ptr>(old_desktop);
    unsigned long long desktop_index = user_desktop->desktop;
    desktop_index = (desktop_index - 1 + m_max_desktops) 
        % m_max_desktops;
    move_to_desktop(client, USER_DESKTOPS[desktop_index], true);
}

/**
 * Changes the current desktop to the desktop after the current.
 */
void ClientModel::next_desktop()
{
    unsigned long long desktop_index = 
        (m_current_desktop->desktop + 1) % m_max_desktops;

    user_desktop_ptr old_desktop = m_current_desktop;
    m_current_desktop = USER_DESKTOPS[desktop_index];

    // We can't change while a window is being moved or resized
    if (m_desktops.count_members_of(MOVING_DESKTOP) > 0 ||
            m_desktops.count_members_of(RESIZING_DESKTOP) > 0)
        return;

    // Only unfocus the current window if it won't be visible
    if (m_focused != None && !is_visible(m_focused))
        unfocus();

    push_change(new ChangeCurrentDesktop(old_desktop, m_current_desktop));
}

/**
 * Changes the current desktop to the desktop before the current.
 */
void ClientModel::prev_desktop()
{
    // We have to add the maximum desktops back in, since C++ doesn't
    // guarantee what will happen with a negative modulus
    unsigned long long desktop_index = 
        (m_current_desktop->desktop - 1 + m_max_desktops) 
        % m_max_desktops;

    user_desktop_ptr old_desktop = m_current_desktop;
    m_current_desktop = USER_DESKTOPS[desktop_index];

    // We can't change while a window is being moved or resized
    if (m_desktops.count_members_of(MOVING_DESKTOP) > 0 ||
            m_desktops.count_members_of(RESIZING_DESKTOP) > 0)
        return;

    // Only unfocus the current window if it won't be visible
    if (m_focused != None && !is_visible(m_focused))
        unfocus();

    push_change(new ChangeCurrentDesktop(old_desktop, m_current_desktop));
}

/**
 * Hides the client and moves it onto the icon desktop.
 */
void ClientModel::iconify(Window client)
{
    desktop_ptr old_desktop = m_desktops.get_category_of(client);

    if (old_desktop->is_icon_desktop())
        return;
    else if (!is_visible(client))
        return;

    m_was_stuck[client] = old_desktop->is_all_desktop();

    move_to_desktop(client, ICON_DESKTOP, true);
}

/**
 * Hides the client and moves it onto the icon desktop.
 */
void ClientModel::deiconify(Window client)
{
    desktop_ptr old_desktop = m_desktops.get_category_of(client);
    if (!old_desktop->is_icon_desktop())
        return;

    // If the client was stuck before it was iconified, then respect that
    // when deiconifying it
    if (m_was_stuck[client])
        move_to_desktop(client, ALL_DESKTOPS, false);
    else
        move_to_desktop(client, m_current_desktop, false);

    // Focus after making the client visible, since a non-visible client
    // cannot be allowed to be focused
    focus(client);
}

/**
 * Starts moving a window.
 */
void ClientModel::start_moving(Window client)
{
    if (!is_visible(client))
        return;

    desktop_ptr old_desktop = m_desktops.get_category_of(client);

    // Only one window, at max, can be either moved or resized
    if (m_desktops.count_members_of(MOVING_DESKTOP) > 0 ||
            m_desktops.count_members_of(RESIZING_DESKTOP) > 0)
        return;

    m_was_stuck[client] = old_desktop->is_all_desktop();
    move_to_desktop(client, MOVING_DESKTOP, true);
}

/**
 * Stops moving a window, and fixes its position.
 */
void ClientModel::stop_moving(Window client, Dimension2D location)
{
    desktop_ptr old_desktop = m_desktops.get_category_of(client);
    if (!old_desktop->is_moving_desktop())
        return;

    if (m_was_stuck[client])
        move_to_desktop(client, ALL_DESKTOPS, false);
    else
        move_to_desktop(client, m_current_desktop, false);

    change_location(client, DIM2D_X(location), DIM2D_Y(location));

    focus(client);
}

/**
 * Starts moving a window.
 */
void ClientModel::start_resizing(Window client)
{
    if (!is_visible(client))
        return;

    desktop_ptr old_desktop = m_desktops.get_category_of(client);

    // Only one window, at max, can be either moved or resized
    if (m_desktops.count_members_of(MOVING_DESKTOP) > 0 ||
            m_desktops.count_members_of(RESIZING_DESKTOP) > 0)
        return;

    m_was_stuck[client] = old_desktop->is_all_desktop();
    move_to_desktop(client, RESIZING_DESKTOP, true);
}

/**
 * Stops resizing a window, and fixes its position.
 */
void ClientModel::stop_resizing(Window client, Dimension2D size)
{
    desktop_ptr old_desktop = m_desktops.get_category_of(client);
    if (!old_desktop->is_resizing_desktop())
        return;

    if (m_was_stuck[client])
        move_to_desktop(client, ALL_DESKTOPS, false);
    else
        move_to_desktop(client, m_current_desktop, false);

    change_size(client, DIM2D_WIDTH(size), DIM2D_HEIGHT(size));

    focus(client);
}

/**
 * Pushes a change into the change buffer.
 */
void ClientModel::push_change(change_ptr change)
{
    if (!m_drop_changes)
        m_changes.push(change);
}

/**
 * Moves a client between two desktops and fires the resulting event.
 */
void ClientModel::move_to_desktop(Window client, desktop_ptr new_desktop, 
        bool unfocus)
{
    desktop_ptr old_desktop = m_desktops.get_category_of(client);
    if (*old_desktop == *new_desktop)
        return;
    m_desktops.move_member(client, new_desktop);

    if (unfocus && !is_visible(client))
        unfocus_if_focused(client);

    push_change(new ChangeClientDesktop(client, old_desktop, new_desktop));
}

/**
 * Starts ignoring changes, until `end_dropping_changes` is called. This is
 * used to ignore changes which occur as a result of specific methods, without
 * having to take some sort of copy-and-restore strategy.
 */
void ClientModel::begin_dropping_changes()
{
    m_drop_changes = true;
}

/**
 * Stops ignoring changes, undoing the effects of `begin_dropping_changes`.
 */
void ClientModel::end_dropping_changes()
{
    m_drop_changes = false;
}
