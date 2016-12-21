# 作者：Forec
# 最后修改日期：2016-12-20
# 邮箱：forec@bupt.edu.cn
# 关于此文件：此文件包含了服务器除认证外的所有的界面入口，包括首页、云盘界面、
#    文件操作、下载、聊天模块、管理员界面等。
# 蓝本：main

import os, random, shutil, zipfile, os.path
from config       import basedir
from datetime     import datetime, timedelta
from sqlalchemy   import or_, and_
from flask        import render_template, session, redirect, url_for, \
                        abort, flash, request, current_app, \
                        make_response, send_from_directory
from flask_login  import login_required, current_user
from .forms       import EditProfileForm, EditProfileAdminForm, \
                        UploadForm, CommentForm, SearchForm, \
                        FileDeleteConfirmForm, ChatForm, \
                        SetShareForm, ConfirmShareForm, \
                        NewFolderForm
from .            import main
from ..           import db
from ..decorators import admin_required, permission_required
from ..models     import User, Role, Permission, File, \
                        Comment, Message,Pagination, CFILE
from werkzeug.utils import secure_filename

# --------------------------------------------------------------------
# 以下列表为服务器支持的不同图标显示格式（视频、图片、文档、压缩包、音频），会
#    使用对应格式的缩略图显示。可在此扩充后缀名以支持更多文件。
# 如果需要增加显示格式，可增加列表，并在对应的模板文件中修改。
# 增加新类别时，需修改的模板文件包括：
#   * file.html
#   * _files.html
#   * _ownfiles.html
#   * _copyownfiles.html
#   * _moveownfiles.html
#   * _forkownfiles.html
videoList = ['.avi', '.mp4', '.mpeg', '.flv', '.rmvb', '.rm', '.wmv']
photoList = ['.jpg', '.jpeg', '.png', '.svg', '.bmp', '.psd']
docList = ['.doc', '.ppt', '.pptx', '.docx', '.xls', '.xlsx', '.txt', '.md', '.rst', '.note']
compressList = ['.rar', '.zip', '.gz', '.gzip', '.tar', '.7z']
musicList = ['.mp3', '.wav', '.wma', '.ogg']

# --------------------------------------------------------------------------
# generateFileTypes 函数根据传入的文件列表，返回一个二元组列表，此列表中每个二元组的
# 第一个元素为传入的文件，第二个元素为该文件所属的文件类型，文件类型用字符串表示，可为：
#  * 'video'：文件后缀名在 videoList 中
#  * 'music'：文件后缀名在 musicList 中
#  * 'txt'：文件后缀名为 '.txt'
#  * 'md'：文件后缀名为 '.md' 或 '.rst'
#  * 'ppt'：文件后缀名为 '.ppt' 或 '.pptx'
#  * 'excel'：文件后缀名为 '.xls' 或 'xlsx'
#  * 'doc'：文件后缀名在 docList 中且不属于以上任何一种
#  * 'photo'：文件后缀名在 photoList 中
#  * 'compress'：文件后缀名在 compressList 中
def generateFileTypes(files):
    file_types = []
    for file in files:
        filetype = 'file'
        suffix = '.'+file.filename.split('.')[-1]
        if suffix in videoList:
            filetype = 'video'
        elif suffix in musicList:
            filetype = 'music'
        elif suffix == '.txt':
            filetype = 'txt'
        elif suffix == '.md' or suffix == '.rst':
            filetype = 'md'
        elif suffix == '.ppt' or suffix == '.pptx':
            filetype = 'ppt'
        elif suffix == '.xls' or suffix == '.xlsx':
            filetype = 'excel'
        elif suffix in docList:
            filetype = 'doc'
        elif suffix in photoList:
            filetype = 'photo'
        elif suffix in compressList:
            filetype = 'compress'
        file_types.append((file, filetype))
    if file_types == []:
        file_types = None
    return file_types

# ---------------------------------------------------------------
# generatePathList 根据传入的一个字符串表示的 *nix 路径，生成此路径的
# 每个父路径和该路径代表的文件夹的名称。如：
# generatePathList('/home/forec/work/') =>
#   [('/', '/'), ('/home/', 'home/'), ('/home/forec/', 'forec/'),
#    ('/home/forec/work/', 'work/')]
def generatePathList(p):
    ans = []
    parts = p.split('/')[:-1]
    sum = ''
    for i in range(0, len(parts)):
        parts[i] = parts[i] + '/'
        sum += parts[i]
        ans.append((sum, parts[i]))
    return ans

# ----------------------------------------------------------------
# moderate 函数提供了 “管理” 界面的入口
@main.route('/moderate')
@admin_required
def moderate():
    return render_template('main/moderate/moderate.html')

# ----------------------------------------------------------------
# home 函数提供了顶点云介绍界面的入口
@main.route('/')
def home():
    return render_template('home.html')

# ----------------------------------------------------------------
# index 为服务器主页入口点，将展示用户共享的资源描述，并保证了对于同一路
# 径下的子目录/文件，只展示顶层路径，如：
#  /
#   - home/
#       - work1/
#           - file1.dat
#           - file2.dat
#       - work2/
# 在以上目录结构中，如果用户 a 共享了目录 /home/ 及该目录下所有文件，则只
# 在 index 界面向其它用户显示用户 a 共享了 /home/，而不会显示 /home/ 目
# 录下的其它目录/文件
@main.route('/index', methods=['GET', 'POST'])
def index():
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
               # 从 cookie 中获取用户的选择，默认显示全部用户的共享文件
    if show_followed:
        query = current_user.followed_files
    else:
        query = File.query.filter("private=0").all()
    page = request.args.get('page', 1, type=int)
    key = request.args.get('key', '', type=str)

    # 关键字搜索表单
    form = SearchForm()
    if form.validate_on_submit():
        return redirect(url_for('main.index',
                                key=form.key.data,
                                _external=True))
    form.key.data = key

    query = sorted(query,
                   key = lambda x: len(x.path),
                   reverse = False)

    filelist = []
    paths_users = []    # 元素为 二元组 (已出现的目录，该路径所属的用户id)
        # 根据路径长度对要显示的文件列表排序，保证顶层目录出现在子目录/文
        # 件之前
    for file in query:
        if file.private == True:
            continue
        if file.path == '/':
            filelist.append(file)
            if file.isdir:
                paths_users.append((file.path+file.filename+'/',
                                    file.ownerid))
        else:
            sappend = True
            for (path, userid) in paths_users:
                if path == file.path[:len(path)] and \
                                userid == file.ownerid:
                    sappend = False
                    break
            if sappend:
                filelist.append(file)
                if file.isdir:
                    paths_users.append((file.path+file.filename+'/',
                                        file.ownerid))
    _filelist = sorted(filelist,
                      key=lambda x:x.created,
                      reverse=True)
        # 按时间对文件排序，最近创建的文件最先显示

    if key == '':
        filelist = _filelist
    else:
        # 用户指定搜索关键词，需对结果做匹配检查
        filelist = []
        for _file in _filelist:
            if key in _file.filename:
                filelist.append(_file)

    pagination = Pagination(page=page,
                            per_page=current_app.\
                                config['ZENITH_FILES_PER_PAGE'],
                            total_count=len(filelist))
    files = filelist[(page-1)*current_app.\
                        config['ZENITH_FILES_PER_PAGE']:
                      page*current_app.\
                        config['ZENITH_FILES_PER_PAGE']]
    return render_template('index/index.html',
                           key =key or '',
                           form = form,
                           files = files,
                           _len = len(files),
                           pagination = pagination,
                           show_followed=show_followed)

# -----------------------------------------------------------------
# show_all 用于将用户 cookie 中的 show_followed 选项复位
# 注意此处不需 login_required
@main.route('/all')
def show_all():
    resp = make_response(redirect(url_for('.index',
                                          _external=True)))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp

# ------------------------------------------------------------------
# show_followed 用于将用户 cookie 中的 show_followed 选项置位
@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index',
                                          _external=True)))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp

# -------------------------------------------------------------------
# user 函数为服务器用户资料界面入口点，用户资料界面包括用户基本信息、
# 资料编辑、共享的资源等内容，其中文件显示方式和 index 界面相同
@main.route('/user/<int:id>')
def user(id):
    user = User.query.filter_by(uid=id).first()
    if user is None:
        abort(404)
    query = user.files.filter_by(private=False).all()
    query = sorted(query,
                   key = lambda x: len(x.path),
                   reverse = False)
        # 将该用户共享的资源按路径长度排序
    page = request.args.get('page', 1, type=int)
    filelist = []
    paths = []
    for file in query:
        if file.private == True:
            continue
        if file.path == '/':
            filelist.append(file)
            if file.isdir:
                paths.append(file.path+file.filename+'/')
        else:
            sappend = True
            for path in paths:
                if path == file.path[:len(path)]:
                    sappend = False
                    break
            if sappend:
                filelist.append(file)
                if file.isdir:
                    paths.append(file.path+file.filename+'/')
    filelist = sorted(filelist,
                      key=lambda x:x.created,
                      reverse=True)
        # 将文件按创建时间排序，最近创建的文件显示在最前
    filelist = generateFileTypes(filelist)
    if filelist is None:
        total_count = 0
    else:
        total_count = len(filelist)
    pagination = Pagination(page=page,
                            per_page=current_app.\
                            config['PROFILE_ZENITH_FILES_PER_PAGE'],
                            total_count=total_count)
    if filelist is not None:
        files = filelist[(page-1)*current_app.\
                            config['PROFILE_ZENITH_FILES_PER_PAGE']:
                          page*current_app.\
                            config['PROFILE_ZENITH_FILES_PER_PAGE']]
    else:
        files = []
    return render_template('main/profile/user.html',
                           user = user,
                           files= files,
                           share_count=total_count,   # 用户共享的资源数量
                           pagination=pagination)

# -----------------------------------------------------------------------
# edit_profile 为当前已登陆用户提供编辑用户资料入口
@main.route('/edit-profile', methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        # 验证上传头像的合法性
        if form.thumbnail.has_file():
            while True:
                # 创建随机目录
                randomBasePath = current_app.\
                    config['ZENITH_TEMPFILE_STORE_PATH'] + \
                    ''.join(random.sample(
                            current_app.\
                                config['ZENITH_RANDOM_PATH_ELEMENTS'],
                            current_app.\
                                config['ZENITH_TEMPFOLDER_LENGTH']))
                if os.path.exists(randomBasePath):
                # 若创建的随机目录已存在则重新创建
                    continue
                break
            os.mkdir(randomBasePath)
            if not os.path.exists(randomBasePath):
                abort(500)
            filepath = os.path.join(randomBasePath,
                                    form.thumbnail.data.filename)
            suffix = form.thumbnail.data.filename
            # 判断后缀名是否合法
            suffix = suffix.split('.')
            if len(suffix) < 2 or '.' + suffix[-1] not in \
                current_app.config['ZENITH_VALID_THUMBNAIL']:
                flash('您上传的头像不符合规范！')
                os.rmdir(randomBasePath)
                return redirect(url_for('main.edit_profile',
                                        _external=True))
            suffix = '.' + suffix[-1]     # suffix 为后缀名

            form.thumbnail.data.save(filepath)
            if not os.path.isfile(filepath):
                abort(500)
            if os.path.getsize(filepath) > \
                current_app.config['ZENITH_VALID_THUMBNAIL_SIZE']:
                # 头像大小大于 512KB
                flash('您上传的头像过大，已被系统保护性删除，请保证'
                      '上传的头像文件大小不超过 ' +
                      str(current_app.\
                          config['ZENITH_VALID_THUMBNAIL_SIZE'] // 1024) +
                      'KB！')
                os.remove(filepath)
                os.rmdir(randomBasePath)
                return redirect(url_for('main.edit_profile',
                                        _external=True))
            else:
                # 验证通过，更新头像
                for _suffix in current_app.config['ZENITH_VALID_THUMBNAIL']:
                    thumbnailPath = os.path.join(basedir,
                                'app/static/thumbnail/' +
                                str(current_user.uid) + _suffix)
                    if os.path.isfile(thumbnailPath):
                        # 之前存在头像则先删除
                        os.remove(thumbnailPath)
                        break

                # 拷贝新头像
                shutil.copy(
                    filepath,
                    os.path.join(basedir,
                        'app/static/thumbnail/' +
                        str(current_user.uid) + suffix)
                )
                # 删除缓存
                os.remove(filepath)
                os.rmdir(randomBasePath)
                current_user.avatar_hash = ':' + \
                    url_for('static',
                           filename = 'thumbnail/' +
                                str(current_user.uid) + suffix,
                           _external=True)

        current_user.nickname = form.nickname.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash('您的资料已更新')
        return redirect(url_for('.user',
                                id=current_user.uid,
                                _external=True))
    form.nickname.data = current_user.nickname
    form.about_me.data = current_user.about_me
    return render_template('main/profile/edit_profile.html', form=form)

# -----------------------------------------------------------------------
# edit_profile_admin 为具有管理员权限的用户提供编辑任意用户资料的入口
@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required     # 限制管理员权限
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.nickname = form.nickname.data
        user.about_me = form.about_me.data
        user.maxm = form.maxm.data
        db.session.add(user)
        flash('用户 ' + user.nickname +' 资料已更新')
        return redirect(url_for('.user',
                                id=user.uid,
                                _external=True))
    form.email.data = user.email
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.maxm.data = user.maxm
    form.nickname.data = user.nickname
    form.about_me.data = user.about_me
    return render_template('main/profile/edit_profile.html', form=form)

# ----------------------------------------------------------------------
# file 显示具体的资源信息，包括资源的类型、大小（如果非目录）、描述、评论以及操作
@main.route('/file/<int:id>', methods=['GET', 'POST'])
def file(id):
    file = File.query.get_or_404(id)
    if file.owner != current_user and \
        file.private == True and \
        not current_user.can(Permission.ADMINISTER):
        # 文件为私有且当前用户非文件所有人且不具有管理员权限则返回 403 错误
        abort(403)
    form =CommentForm()
    if form.validate_on_submit():
        comment = Comment(body = form.body.data,
                          file = file,
                          author = current_user._get_current_object())
        db.session.add(comment)
        flash('您的评论已发布')
        return redirect(url_for('.file',
                                id=file.uid,
                                page=-1,
                                _external=True))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (file.comments.count() - 1)// \
            current_app.config['ZENITH_COMMENTS_PER_PAGE'] + 1
    pagination = file.comments.order_by(Comment.timestamp.asc()).\
        paginate(page,
                 per_page=current_app.config['ZENITH_COMMENTS_PER_PAGE'],
                 error_out=False)   # 对评论分页
    pathLists = generatePathList(file.path)
    file_type = generateFileTypes([file])[0][1] # 获取当前显示文件的文件类型
    comments = pagination.items
    return render_template('main/files/file.html',
                           comments = comments,
                           file_type=file_type,
                           pathlists = pathLists,
                           pagination = pagination,
                           file = file,
                           form = form,
                           moderate=current_user.\
                           can(Permission.MODERATE_COMMENTS))

# -----------------------------------------------------------------------
# follow 为用户关注其它用户提供了跳板，若关注成功则跳转到被关注用户的资料界面，否
# 则跳转到主页。用户须具有 follow 权限才可关注（需认证邮箱）
@main.route('/follow/<int:id>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(id):
    user = User.query.filter_by(uid=id).first()
    if user is None:
        flash('不合法的用户')
        return redirect(url_for('.index',
                                _external=True))
    if current_user.is_following(user):
        flash('您已关注该用户')
        return redirect(url_for('.user',
                                id=user.uid,
                                _external=True))
    current_user.follow(user)
    flash('您已关注用户 %s' % user.nickname)
    return redirect(url_for('.user',
                            id=user.uid,
                            _external=True))

# --------------------------------------------------------------------
# unfollow 为用户提供了 follow 的逆操作
@main.route('/unfollow/<int:id>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(id):
    user = User.query.filter_by(uid=id).first()
    if user is None:
        flash('不合法的用户')
        return redirect(url_for('.index',
                                _external=True))
    if not current_user.is_following(user):
        flash('您并未关注该用户')
        return redirect(url_for('.user',
                                uid=id,
                                _external=True))
    current_user.unfollow(user)
    flash('您已取消对用户 %s 的关注' % user.nickname)
    return redirect(url_for('.user',
                            uid=id,
                            _external=True))

# --------------------------------------------------------------------
# followers 提供了显示某用户关注者的界面入口
@main.route('/followers/<int:id>')
def followers(id):
    user = User.query.filter_by(uid=id).first()
    if user is None:
        flash('不合法的用户')
        return redirect(url_for('.index',
                                _external=True))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.\
        paginate(page,
                 per_page=current_app.\
                    config['ZENITH_FOLLOWERS_PER_PAGE'],
                 error_out=False)
    follows = [{
                   'user'     : item.follower,
                   'timestamp': item.timestamp
               }
               for item in pagination.items]
    return render_template('main/profile/followers.html',
                           user=user,
                           title="的关注者",
                           endpoint='.followers',
                           pagination=pagination,
                           follows=follows)

# --------------------------------------------------------------------
# followed_by 提供了显示某用户关注的人的入口
@main.route('/followed-by/<int:id>')
def followed_by(id):
    user = User.query.filter_by(uid=id).first()
    if user is None:
        flash('不合法的用户')
        return redirect(url_for('.index',
                                _external=True))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.\
        paginate(page,
                 per_page=current_app.\
                    config['ZENITH_FOLLOWERS_PER_PAGE'],
                 error_out=False)
    follows = [{
                   'user'     : item.followed,
                   'timestamp': item.timestamp
               }
               for item in pagination.items]
    return render_template('main/profile/followers.html',
                           user=user,
                           title="关注的人",
                           endpoint='.followed_by',
                           pagination=pagination,
                           follows=follows)

# --------------------------------------------------------------------
# delete_file 为用户提供了删除文件界面的入口，用户需对自己的删除操作进行
# 确认后，方可产生一个一次性的 token，并使用此 token 跳转到 delete_fil-
# e_confirm 入口执行删除操作。
@main.route('/delete-file/<int:id>', methods=['GET','POST'])
@login_required
def delete_file(id):
    file= File.query.get_or_404(id)
    if current_user != file.owner and \
        not current_user.can(Permission.ADMINISTER):
        abort(403)
    flash('小心！删除操作不能撤回！')
    form = FileDeleteConfirmForm()
    if form.validate_on_submit():
        if form.filename.data == '' or \
            form.filename.data is None:
            flash("文件名不合法！")
            return redirect(url_for('.file',
                                    id=file.uid,
                                    _external=True))
        file.filename = form.filename.data
        file.description = form.body.data
        db.session.add(file)
        if file.isdir:
            flash('目录信息已被更新')
        else:
            flash('文件信息已被更新')
        return redirect(url_for('.file',id = file.uid, _external=True))
    form.body.data=file.description
    form.filename.data = file.filename
    return render_template('main/files/confirm_delete_file.html',
                           file = file,
                           form=form,
                           token=current_user.\
                            generate_delete_token(fileid=id,
                                                  expiration=3600))
                    # generate_delete_token 方法为用户模型定义方法，
                    # 生成一个一次性、有效期一小时的token

# ------------------------------------------------------------------------
# delete_file_confirm 函数对用户的删除操作进行确认并执行。当前用户对 URL 中的
# token 做解析，若解析失败或不具备相应权限则返回 403 错误，否则将删除写入数据库
# 若用户删除的是目录，delete_file_confirm 会将此目录下所有关联文件删除
@main.route('/delete-file-confirm/<token>')
@login_required
def delete_file_confirm(token):
    returnURL, uid = current_user.delete_file(token)
        # 由用户的自定义方法 delete_file 删除此文件/目录，该自定义方法会识别
        # 要删除的是文件/文件夹并删除关联文件
    if returnURL is not None:
        flash('成功删除！')
        if current_user.can(Permission.ADMINISTER) and \
            uid != current_user.uid:
            return redirect(url_for('main.moderate_files',
                                    _external=True))
        else:
            return redirect(url_for('main.cloud',
                                    path=returnURL,
                                    direction='front',
                                    type='all',
                                    _external=True))
    else:
        abort(403)

# -----------------------------------------------------------------------
# edit_file 函数为用户编辑文件信息（重命名、修改描述）界面提供了入口
@main.route('/edit-file/<int:id>', methods=['GET','POST'])
@login_required
def edit_file(id):
    file= File.query.get_or_404(id)
    if current_user != file.owner and \
        not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = FileDeleteConfirmForm()
    if form.validate_on_submit():
        if form.filename.data == '' or \
            form.filename.data is None:
            flash("文件名不合法！")
            return redirect(url_for('.file',
                                    id=file.uid,
                                    _external=True))
        _file = File.query.\
            filter('filename=:lfn and ownerid=:_id and path=:_path').\
            params(lfn = form.filename.data,
                   _id = current_user.uid,
                   _path = file.path).first()
        if _file is not None and _file.uid != file.uid:
            # 目录下已存在与新文件名同名的文件/目录
            flash('当前目录下已存在与您新指定的名称同名的文件/目录！')
            return redirect(url_for('main.edit_file',
                                    id=file.uid,
                                    _external=True))
        file.filename = form.filename.data
        file.description = form.body.data
        db.session.add(file)
        if file.isdir:
            flash('目录信息已被更新')
        else:
            flash('文件信息已被更新')
        return redirect(url_for('.file',
                                id = file.uid,
                                _external=True))
    form.body.data=file.description
    form.filename.data = file.filename
    return render_template('main/files/edit_file.html',
                           file = file,
                           form=form)

# ----------------------------------------------------------------------
# moderate_comments 为评论管理员提供了审核、屏蔽评论的界面入口
# 具有审核评论权限的用户可以访问此入口
# 此界面提供按关键字搜索评论的功能
@main.route('/moderate_comments', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_comments():
    form = SearchForm()
    if form.validate_on_submit():
        return redirect(url_for('main.moderate_comments',
                                key=form.key.data,
                                _external=True))
    page = request.args.get('page', 1, type=int)
    key = request.args.get('key', '', type=str)
    if key == '':
        comment = Comment.query
    else:
        comment = Comment.query.\
            filter(Comment.body.like('%'+key+'%'))
        # 当评论管理员指定关键字时，按关键字搜索相关评论
    pagination = comment.order_by(
            Comment.timestamp.desc()).\
            paginate(page,
                     per_page=current_app.\
                     config['ZENITH_COMMENTS_PER_PAGE'],
                     error_out=False)
    comments = pagination.items
    form.key.data = key
    return render_template('main/moderate/moderate_comments.html',
                           page=page,
                           form=form,
                           comments=comments,
                           pagination=pagination)

# ------------------------------------------------------------------
# moderate_comments_disable 为评论管理员提供了将某条评论屏蔽的入口
@main.route('/moderate_comments/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_comments_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate_comments',
                            page=request.args.\
                                get('page', 1, type=int),
                            _external=True))

# --------------------------------------------------------------------
# moderate_comments_enable 为评论管理员提供了将某条评论取消屏蔽的入口
# 是 moderate_comments_disable 的逆操作
@main.route('/moderate_comments/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_comments_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate_comments',
                            page=request.args.\
                                get('page', 1, type=int)))

# --------------------------------------------------------------------
# moderate_comments_disable_own 为文件所有者提供了管理自己文件下评论的
# 权限，用户可以删除自己文件下的评论。对用户来说，此操作不可逆。
@main.route('/moderate_comments/disable_own/<int:id>')
@login_required
def moderate_comments_disable_own(id):
    comment = Comment.query.get_or_404(id)
    if comment.author == current_user or \
       comment.file.owner == current_user:
        comment.disabled = True
        db.session.add(comment)
        flash('评论已被设置为不可见')
        return redirect(url_for('.file',
                                id = comment.file_id,
                                _external=True))

# --------------------------------------------------------------------
# moderate_files 为管理员提供了修改、删除、设置任意文件状态的入口
# 用户必须具有管理员权限才可访问此页面，否则返回 403 错误
@main.route('/moderate_files', methods=['GET', 'POST'])
@login_required
@admin_required
def moderate_files():
    form = SearchForm()
    if form.validate_on_submit():
        return redirect(url_for('main.moderate_files',
                                key=form.key.data,
                                _external=True))
    page = request.args.get('page', 1, type=int)
    key = request.args.get('key', '', type=str)
    if key == '':
        file = File.query
    else:
        file = File.query.filter(or_(File.filename.\
                                        like('%'+key+'%'),
                                     File.description.\
                                        like('%'+key+'%')))
        # 当管理员指定关键字时，按关键字搜索相关文件/目录。关键字搜索的
        # 区域包括文件/目录名及其描述
    pagination = file.order_by(File.created.desc()).\
        paginate(page,
                 error_out=False,
                 per_page=current_app.\
                    config['ZENITH_FILES_PER_PAGE'])
    files = pagination.items
    form.key.data = key
    return render_template('main/moderate/moderate_files.html',
                           files=files,
                           page=page,
                           form=form,
                           pagination=pagination)

# --------------------------------------------------------------------
# moderate_files_delete 为管理员用户提供了删除文件的入口，管理员也可以
# 通过用户的 delete_file 来实现此功能，但此方式去掉了认证阶段。默认的模板
# 中，管理员删除操作均指向此入口，通过修改模板中的 moderate_files_delete 为
# delete_file，可以增加删除认证界面。涉及的模板包括：
#   * file.html
#   * _files.html
#   * _ownfiles.html
#   * _copyownfiles.html
#   * _moveownfiles.html
#   * _forkownfiles.html
@main.route('/moderate_files/disable/<int:id>')
@login_required
@admin_required
def moderate_files_delete(id):
    file = File.query.get_or_404(id)
    return redirect(url_for('main.delete_file_confirm',
                            token=current_user.\
                                generate_delete_token(
                                    fileid=id,
                                    expiration=3600
                            ),
                            _external=True
                        )
                    )

# -------------------------------------------------------------------
# messages 函数是用户消息界面的入口，提供了用户与其它用户交流的消息缩略，
# 类似 Wechat 的主界面，与每个用户的聊天只显示最近的一条消息，并会标明
# 是否有消息未读。若有则模板中的消息提示栏会显示未读数目（即当前有多少个
# 用户的消息未读）。
# 用户可在此界面按关键字搜索消息，搜索范围包括所有发送和接收到的消息内容。
@main.route('/messages/', methods=['GET', 'POST'])
@login_required
def messages():
    form = SearchForm()
    if form.validate_on_submit():
        return redirect(url_for('main.messages',
                                key=form.key.data,
                                _external=True))
    key = request.args.get('key', '', type=str)
    page = request.args.get('page', 1, type=int)
    pagination = None
    form.key.data = key
    if key == '':   # 用户没有按关键字搜索，则显示消息主界面
        uncheck_messages = Message.query.\
            filter("(sendid=:sid and send_delete=0) or"
                   " (targetid=:sid and recv_delete=0)").\
            params(sid=current_user.uid).\
            order_by(Message.created.desc()).all()
            # 获取所有和当前用户相关的消息并按创建时间从近到远排序
        messageList = []
        chatUserIdList = []
            # 为了对每个用户只显示最近的消息，使用 chatUserIdList 保存
            # 当前已经存在最近消息的用户 Id。因为消息已按创建时间排序，因
            # 此若 chatUserIdList 中存在某个用户 Id 而又检索到和该用户
            # 交互的消息，则该消息一定晚于已加入 messageList 的消息。
            # messageList 用于记录最近消息。
        for message in uncheck_messages:
            if message.sender.uid == current_user.uid:
                targetid = message.receiver.uid
            else:
                targetid = message.sender.uid
            find = False
            for i in range(0, len(chatUserIdList)):
                if targetid == chatUserIdList[i]:
                    find = True
                    if current_user == message.receiver and \
                        message.viewed == False:
                        messageList[i][1] += 1
                        # 若某条消息未读且接收者为当前用户，则这条消息的
                        # 发送方向当前用户发送的未读消息数加 1
                    break
            if not find:
                # 若 chatUserIdList 未找到该用户 Id 则加入消息和 Id
                chatUserIdList.append(targetid)
                if not message.viewed and \
                    current_user == message.receiver:
                    messageList.append([message, 1])
                    # 若要加入的消息未读，且该消息的接收者为当前用户，
                    # 则将该消息未读数置 1
                else:
                    messageList.append([message, 0])
        _message = messageList
    else:       # 用户指定了搜索关键字，则搜索和关键字匹配的全部消息
        _messages = Message.query.\
                        filter(and_(Message.message.\
                                        like('%' + key + '%'),
                                    or_(Message.receiver==current_user,
                                        Message.sender==current_user)))
        pagination = _messages.order_by(Message.created.desc()).\
            paginate(page,
                     per_page=current_app.\
                        config['ZENITH_MESSAGES_PER_PAGE'],
                     error_out=False)
            # 按关键字搜索时，需要对检索到的结果分页显示
        _message = []
        for message in  pagination.items:
            _message.append((message, 0))
        if _message == []:
            _message = None
    return render_template('main/messages/messages.html',
                           key=key,
                           form=form,
                           page=page,
                           messages = _message,
                           pagination=pagination)

# --------------------------------------------------------------------------
# cloud 函数提供了“我的云盘”界面入口
@main.route('/cloud/', methods=['GET', 'POST'])
@login_required
def cloud():
    # generateFilelike 函数根据传入的 list 中包含的文件后缀名，生成
    # 对应的 SQL 查询语句，用于按类型（文件后缀名）索引文件
    def generateFilelike(list):
        string = ""
        for suffix in list:
            string += "or filename like '%" + \
                      suffix + "' "
        return '('+string[3:]+')'
    type = request.args.get('type', 'all', type=str)
        # 用户指定的文件类型，默认为 'all'
    path = request.args.get('path', '/', type=str)
        # 用户当前访问的目录，默认为根目录 '/'
    key = request.args.get('key', '', type=str)
        # 用户指定的检索关键字，默认为空
    order = request.args.get('order', 'time', type=str)
        # 用户指定的排序方式，默认为按照创建时间排序
    direction = request.args.get('direction', 'front', type=str)
        # 用户指定的顺序，默认为正序
    page = request.args.get('page', 1, type=int)
        # 界面需要分页，用户当前要访问的页数
    if path == '':
        path = '/'

    # 当路径不为根目录时，检查该路径对于当前用户是否合法（该用户是否已创建该目录）
    if path != '/':
        if len(path.split('/')) < 3 or path[-1] != '/':
            abort(403)
        ___filename = path.split('/')[-2]
        ___filenameLen = -(len(___filename)+1)
        ___path = path[:___filenameLen]
        isPath = File.query.filter("path=:p and isdir=1 "
                                   "and filename=:f and ownerid=:d").\
                            params(p=___path,
                                   f=___filename,
                                   d=current_user.uid).first()
        if isPath is None or isPath.owner != current_user:
            abort(403)

    # 生成搜索表单，当用户提交时跳转并查询
    form = SearchForm()
    if form.validate_on_submit():
        return redirect(url_for('main.cloud',
                                key = form.key.data,
                                page=page,
                                path=path,
                                type=type,
                                order=order,
                                direction=direction,
                                _external=True
                                ))
    form.key.data = key

    # 无论用户是否指定关键词，先根据用户指定的文件类型，查询对应的文件
    if type == 'video':
        query = current_user.files.filter(generateFilelike(videoList))
    elif type == 'document':
        query = current_user.files.filter(generateFilelike(docList))
    elif type == 'photo':
        query = current_user.files.filter(generateFilelike(photoList))
    elif type == 'music':
        query = current_user.files.filter(generateFilelike(musicList))
    elif type == 'compress':
        query = current_user.files.filter(generateFilelike(compressList))
    else:
        query = current_user.files.filter("path=:p").params(p=path)

    # 确保只显示属于当前用户的目录和文件
    query = query.filter("ownerid=:_oid").params(_oid=current_user.uid)

    if key != '':
        # 当用户指定关键字时，在当前目录下递归检索所有可能文件。
        if type in ['video', 'document', 'photo', 'music',
                        'compress']:
            # 若用户已指定查询类型
            query = query.\
                filter("filename like :lfn and "
                     "ownerid=:id and path like :_path").\
                      params(lfn = '%' + key + '%',
                             id = current_user.uid,
                             _path = path + '%')
        else:
            # 用户未指定查询类型时在整个目录下递归检索
            query = File.query.\
                filter("filename like :lfn and "
                     "ownerid=:_suid and path like :_path").\
                      params(lfn = '%' + key + '%',
                             _suid = current_user.uid,
                             _path = path + '%')

    # 按用户指定顺序对文件排序
    if order == 'name':
        if direction == 'reverse':
            query = query.order_by(File.filename.desc())
        else:
            query = query.order_by(File.filename.asc())
    else:
        if direction == 'reverse':
            query = query.order_by(File.created.asc())
        else:
            query = query.order_by(File.created.desc())

    # 对文件列表分页
    pagination = query.paginate(
        page, per_page=current_app.config['ZENITH_FILES_PER_PAGE'],
        error_out=False
    )
    files = pagination.items
    file_types = generateFileTypes(files)
    return render_template('main/cloud/cloud.html',
                           files = file_types,
                           _type=type,
                           form=form,
                           _order=order,
                           key = key,
                           _path=path,
                           _direction=direction ,
                           pagination = pagination,
                           pathlists=generatePathList(path))

# ------------------------------------------------------------------------------
# view_share_folder_entry 函数提供了用户访问其他用户共享目录的认证入口。用户须
# 在此界面验证（如果共享目录存在共享密码）
@main.route('/check-share-folder/<int:id>', methods=['GET', 'POST'])
@login_required
def view_share_folder_entry(id):
    file = File.query.get_or_404(id)
    if file is None or (file.private == True and \
                        file.owner != current_user and \
                        not current_user.can(Permission.ADMINISTER)):
    # 当文件不存在/文件为私有且不属于当前用户且当前用户不具有
    # 管理员权限时，返回403错误
        abort(403)
    if file.linkpass is None or file.linkpass == '' or \
        file.owner == current_user or \
        current_user.can(Permission.ADMINISTER):
        # 文件未设置共享密码或属于当前用户或当前用户具有管理员权限，直接跳转到查看界面
        return redirect(url_for('main.view_do',
            token=current_user.generate_view_token(rootid=file.uid,
                                                   type='all',
                                                   order='time',
                                                   direction='front',
                                                   key='',
                                                   path=file.path +
                                                        file.filename +
                                                        '/',
                                                   _linkpass=file.linkpass,
                                                   expiration=3600),
            _external=True))
    form = ConfirmShareForm()
    if form.validate_on_submit():
        if form.password.data == file.linkpass:
            # 文件提取码正确
            return redirect(url_for('main.view_do',
                token=current_user.generate_view_token(rootid=file.uid,
                                                       type='all',
                                                       order='time',
                                                       direction='front',
                                                       key='',
                                                       path=file.path +
                                                            file.filename +
                                                            '/',
                                                       _linkpass=file.linkpass,
                                                       expiration=3600),
                _external=True))
        else:
            flash('提取码错误！')
            return redirect(url_for('main.view_share_folder_entry',
                                    id=file.uid,
                                    _external=True))
    return render_template('main/share/view_verify.html',
                           file=file,
                           form=form)

# ------------------------------------------------------------------------------
# view_do 为用户提供了访问其他用户共享目录的界面。
@main.route('/view-do/', methods=['GET', 'POST'])
@login_required
def view_do():
    # generateFilelike 函数根据传入的 list 中包含的文件后缀名，生成
    # 对应的 SQL 查询语句，用于按类型（文件后缀名）索引文件
    def generateFilelike(list):
        string = ""
        for suffix in list:
            string += "or filename like '%" + \
                      suffix + "' "
        return '('+string[3:]+')'

    # generateSharedPathList 是 generatePathList 函数的另一版本，此
    # 函数不生成根目录，而是以用户共享的目录为根。
    def generateSharedPathList(basePath, path):
        toDisplay = path[len(basePath):].split('/')[:-1]
        # /home/forec/ 下的共享目录 /home/forec/work/***
        # 则要显示给用户的目录为 work/***
        pathList = []
        base = ""
        for folder in toDisplay:
            pathList.append((basePath + base + folder + '/',
                             folder + '/'))
            base += folder + '/'
        return pathList

    token = request.args.get('token', None, type=str)
    page = request.args.get('page', 1, type=int)
        # 界面需要分页，用户当前要访问的页数
    if token is None:
        abort(403)

    args = current_user.view_token_verify(token)
    if args is None:
        abort(403)
    type = args.get('type') or 'all'
        # 用户指定的文件类型，默认为 'all'
    key = args.get('key') or ''
        # 用户指定的检索关键字，默认为空
    order = args.get('order') or 'time'
        # 用户指定的排序方式，默认为按照创建时间排序
    direction = args.get('direction') or 'front'
        # 用户指定的顺序，默认为正序
    path = args.get('path')
        # 用户当前访问的总路径
    fileid = args.get('rootid')
        # 用户当前要访问的目录 Id
    password = args.get('password')
        # 该目录的共享密码
    rootfile = File.query.get(fileid)

    # 检验访问的合法性
    if rootfile is None or \
        (rootfile.owner != current_user and \
        (rootfile.private or rootfile.linkpass != password) and \
         not current_user.can(Permission.ADMINISTER)):
        # 文件不存在 或
        # 文件不属于当前用户且 文件为私有或提取码不正确 且 当前
        # 用户不具备管理员权限
        abort(403)
    if not rootfile.isdir:
        return redirect(url_for('main.file',
                                id=file.uid,
                                _external=True))
    if rootfile.isdir and rootfile.owner == current_user:
        # 当前用户持有该目录
        return redirect(url_for('main.cloud',
                                path=rootfile.path +
                                     rootfile.filename +
                                     '/',
                                _external=True))
    # 修正不合法的路径
    if path is None or path == '':
        path = rootfile.path +\
               rootfile.filename +\
               '/'

    # 当路径不为根目录时，检查该路径对于当前用户是否合法（该用户是否已创建该目录）
    if path != '/':
        if len(path.split('/')) < 3 or path[-1] != '/':
            abort(403)
        ___filename = path.split('/')[-2]
        ___filenameLen = -(len(___filename)+1)
        ___path = path[:___filenameLen]
        isPath = File.query.filter("path=:p and isdir=1 "
                                   "and filename=:f and ownerid=:d").\
                            params(p=___path,
                                   f=___filename,
                                   d=rootfile.ownerid).first()
        if isPath is None or \
           (isPath.private and \
            not current_user.can(Permission.ADMINISTER)) or \
           (password != isPath.linkpass and \
            not current_user.can(Permission.ADMINISTER)):
            # 目录不存在或 目录为私有且当前用户非管理员 或
            # 目录提取码不正确且当前用户非管理员
            abort(403)
        if isPath.owner == current_user:
            return redirect(url_for('main.cloud',
                                    path = path,
                                    _external=True))

    if isPath is None:
        abort(403)
    currentFolder = isPath

    # 生成搜索表单，当用户提交时跳转并查询
    form = SearchForm()
    if form.validate_on_submit():
        return redirect(url_for('main.view_do',
                token=current_user.generate_view_token(
                                key = form.key.data,
                                rootid = rootfile.uid,
                                _linkpass =
                                    currentFolder.linkpass,
                                path = path,
                                type = type,
                                order = order,
                                direction = direction,
                                expiration=3600
                ),
                page = page,
                _external=True))
    form.key.data = key

    # 无论用户是否指定关键词，先根据用户指定的文件类型，查询对应的文件
    if type == 'video':
        query = rootfile.owner.files.\
            filter(generateFilelike(videoList))
    elif type == 'document':
        query = rootfile.owner.files.\
            filter(generateFilelike(docList))
    elif type == 'photo':
        query = rootfile.owner.files.\
            filter(generateFilelike(photoList))
    elif type == 'music':
        query = rootfile.owner.files.\
            filter(generateFilelike(musicList))
    elif type == 'compress':
        query = rootfile.owner.files.\
            filter(generateFilelike(compressList))
    else:
        query = rootfile.owner.files.\
            filter("path=:p").params(p=path)

    # 确保只显示属于共享用户的共享目录和文件
    # 代码中的 _path 不可被修改为其他占位符！
    query = query.\
        filter("ownerid=:oid and private=0 and "
               "path like :_path and linkpass=:_link").\
        params(oid=rootfile.ownerid,
               _path=path+'%',
               _link=rootfile.linkpass)

    if key != '':
        # 当用户指定关键字时，在当前目录下递归检索所有可能文件。
        if type in ['video', 'document', 'photo', 'music',
                        'compress']:
            # 若用户已指定查询类型
            query = query.\
                filter("filename like :lfn and "
                     "ownerid=:id and path like :_path").\
                      params(lfn = '%' + key + '%',
                             id = rootfile.ownerid,
                             _path = path + '%')
        else:
            # 用户未指定查询类型时在整个目录下递归检索
            query = File.query.\
                filter("filename like :lfn and "
                     "ownerid=:id and path like :_path").\
                      params(lfn = '%' + key + '%',
                             id = rootfile.ownerid,
                             _path = path + '%')

    # 按用户指定顺序对文件排序
    if order == 'name':
        if direction == 'reverse':
            query = query.order_by(File.filename.desc())
        else:
            query = query.order_by(File.filename.asc())
    else:
        if direction == 'reverse':
            query = query.order_by(File.created.asc())
        else:
            query = query.order_by(File.created.desc())

    # 对文件列表分页
    pagination = query.paginate(
        page, per_page=current_app.config['ZENITH_FILES_PER_PAGE'],
        error_out=False
    )
    files = pagination.items
    file_types = generateFileTypes(files)

    return render_template('main/share/viewShares.html',
                           files = file_types,
                           form= form,
                           _type= type or 'all',
                           _order= order or 'time',
                           key = key or '',
                           rootfile = rootfile,
                           path= path,
                           _direction= direction or 'front',
                           pagination = pagination,
                           pathlists= generateSharedPathList(
                                   rootfile.path,
                                   path
                           ))

# ------------------------------------------------------------------------------
# download 函数为设有分享密码的文件/目录提供了验证界面，否则直接跳转到 download_do 入口。
@main.route('/download/<int:id>', methods=['GET', 'POST'])
@login_required
def download(id):
    file = File.query.get_or_404(id)
    if file is None or (file.private == True and \
                        file.owner != current_user and \
                        not current_user.can(Permission.ADMINISTER)):
    # 当文件不存在/文件为私有且不属于当前用户且当前用户不具有
    # 管理员权限时，返回403错误
        abort(403)
    if file.linkpass is None or file.linkpass == '' or \
        file.owner == current_user or \
        current_user.can(Permission.ADMINISTER):
        # 文件未设置共享密码或属于当前用户或当前用户为管理员，直接跳转到下载界面
        return redirect(url_for('main.download_do',
            token=current_user.generate_download_token(file.uid,
                                                       file.linkpass,
                                                       expiration=3600),
            _external=True))
    form = ConfirmShareForm()
    if form.validate_on_submit():
        if form.password.data == file.linkpass:
            # 文件提取码正确
            return redirect(url_for('main.download_do',
                token=current_user.generate_download_token(file.uid,
                                                           file.linkpass,
                                                           expiration=3600),
                _external=True))
        else:
            flash('提取码错误！')
            return redirect(url_for('main.download',
                                    id=file.uid,
                                    _external=True))
    return render_template('main/load/download_verify.html',
                           file=file,
                           form=form)

# --------------------------------------------------------------------------
# download_do 函数验证用户的下载请求是否合法，传入的 token 将由当前用户进
# 行解析，若失败则返回 403 错误；若成功则根据用户请求反馈数据，当用户试图下
# 载的是目录时，会先将目录压缩为压缩包后反馈给用户，否则直接返回文件。
@main.route('/download_do/<token>')
@login_required
def download_do(token):
    fileid_pass = current_user.download_token_verify(token)
        # 用户模型自定义方法，解析 token 并返回一个列表，列表包含两个元素，
        # 分别为文件的 uid 和用户提供的提取码
    # 当解析出的结果或结果包含的 uid 为空时说明 token 为伪造，返回 403 错误
    if fileid_pass is None:
        abort(403)
    _fileid = fileid_pass[0]
    _pass = fileid_pass[1]
    if _fileid is None:
        abort(403)
    if _pass is None:
        _pass = ''

    file = File.query.get_or_404(_fileid)
    if file is None or \
            (file.private == True and \
             file.owner != current_user and \
             not current_user.can(Permission.ADMINISTER)) or \
            (file.private == False and \
             file.linkpass != _pass and \
             current_user != file.owner and \
             not current_user.can(Permission.ADMINISTER)):
        # uid 对应的文件不存在  或
        # 文件为私有且当前用户不是文件所有者且当前用户不具备管理员权限 或
        # 文件为公有且 token 解析的提取码与实际提取码不同且当前用户不是文件所有者
        abort(403)

    # 若不是目录且文件为空则返回空文件（服务器的 init
    #    操作会保证存储路径下文件 '0' 为空文件）
    if file.cfileid == -1 and not file.isdir:
        f = open(current_app.\
                    config['ZENITH_FILE_STORE_PATH'] + '0',
                 'rb')
        data = f.read()
        response = make_response(data)
        response.headers["Content-Disposition"] = \
            ("attachment; filename=" + file.filename).encode('utf-8')
        return response

    # 若要下载的不是目录且文件不为空
    elif not file.isdir:
        # 增加文件下载记录
        file.downloaded += 1
        db.session.add(file)
        cfile = CFILE.query.get_or_404(file.cfileid)
        if not os.path.exists(current_app.\
                config['ZENITH_FILE_STORE_PATH'] + str(cfile.uid)):
            # 若服务器存储文件路径下不存在要下载的文件则返回 500 错误
            abort(500)
        f = open(current_app.\
                    config['ZENITH_FILE_STORE_PATH'] + str(cfile.uid),
                 'rb')
        data = f.read()
        response = make_response(data)
        response.headers["Content-Disposition"] = \
            ("attachment; filename=" + file.filename).encode('utf-8')
        return response

    # 用户试图下载目录，则在 TEMP 目录下新建一个目录，该目录名称
    #    长 ZENITH_TEMPFOLDER_LENGTH 位，由字母和数字随机生成
    else:
        while True:
            randomBasePath = current_app.\
                config['ZENITH_TEMPFILE_STORE_PATH'] + \
                ''.join(random.sample(current_app.config['ZENITH_RANDOM_PATH_ELEMENTS'],
                                      current_app.config['ZENITH_TEMPFOLDER_LENGTH']))
            if os.path.exists(randomBasePath):
            # 若创建的随机目录已存在则重新创建
                continue
            os.mkdir(randomBasePath)
            randomBasePath += current_app.config['ZENITH_PATH_SEPERATOR']
            break

        if file.owner == current_user:
            # 用户为目录所有者，则可以直接下载目录下全部文件
            subFolderList = File.query.\
                filter("path like :p and ownerid=:d and isdir=1").\
                params(p = file.path + file.filename + '/%',
                       d = current_user.uid).all()
            subFolderList = sorted(subFolderList,
                                   key = lambda x:len(x.path),
                                   reverse = False)
            subFileList = File.query.\
                filter("path like :p and ownerid=:d and isdir=0").\
                params(p = file.path + file.filename + '/%',
                       d = current_user.uid).all()
        else:
            # 用户试图下载其他用户共享的目录，则需过滤目录下的私有文件
            subFolderList = File.query.\
                filter("path like :p and ownerid=:d "
                       "and isdir=1 and private=0").\
                params(p = file.path + file.filename + '/%',
                       d = file.ownerid).all()
            subFolderList = sorted(subFolderList,
                                   key = lambda x:len(x.path),
                                   reverse = False)
            subFileList = File.query.\
                filter("path like :p and ownerid=:d "
                       "and isdir=0 and private=0").\
                params(p = file.path + file.filename + '/%',
                       d = file.ownerid).all()
        subFolderList.insert(0, file)

        # 在随机生成的目录下创建整个目录结构
        basePathLen = len(file.path)
        for _folder in subFolderList:
            # 增加目录下载记录
            _folder.downloaded += 1
            db.session.add(_folder)
            dirName = (_folder.path + _folder.filename)[basePathLen:].\
                replace('/', current_app.config['ZENITH_PATH_SEPERATOR'])
                # 需根据服务器设置将 *nix 路径替换为服务器所在系统的路径分隔符
            os.mkdir(randomBasePath + dirName)
            if not os.path.exists(randomBasePath + dirName):
                # 目录未能成功创建，返回 500 错误
                abort(500)

        # 已创建完成目录结构，将文件拷贝到指定位置并重命名
        for _file in subFileList:
            # 增加文件下载记录
            _file.downloaded += 1
            db.session.add(_file)
            fileName = (_file.path + _file.filename)[basePathLen:].\
                replace('/', current_app.config['ZENITH_PATH_SEPERATOR'])
            cfileName = _file.cfileid
            if cfileName < 0:  # 空文件
                cfileName = 0
            shutil.copy(current_app.\
                            config['ZENITH_FILE_STORE_PATH'] +
                            str(cfileName),
                        randomBasePath + fileName)
            if not os.path.exists(randomBasePath + fileName):
                # 文件未能成功复制，返回 500 错误
                abort(500)

        # zip_dir 可将文件/目录压缩为指定名称的压缩文件
        def zip_dir(dirname, zipfilename):
            toZipFilelist = []
            toZipFilelist.append(dirname)
            if not os.path.isfile(dirname):
                for root, dirs, files in os.walk(dirname):
                    for name in dirs:
                        toZipFilelist.append(os.path.join(root, name))
                    for name in files:
                        toZipFilelist.append(os.path.join(root, name))

            zf = zipfile.ZipFile(zipfilename, "w", zipfile.zlib.DEFLATED)
            for tar in toZipFilelist:
                arcname = tar[len(dirname):]
                zf.write(tar, arcname)
            zf.close()

        # 压缩
        try:
            zip_dir(randomBasePath + file.filename,
                randomBasePath + file.filename + '.zip')
        except:
            abort(500)
        if not os.path.exists(randomBasePath + file.filename + '.zip'):
            # 压缩失败
            abort(500)
        f = open(randomBasePath + file.filename + '.zip',
                 'rb')
        data = f.read()
        response = make_response(data)
        response.headers["Content-Disposition"] = \
            ("attachment; filename=" + file.filename +'.zip').encode('utf-8')
        return response

# --------------------------------------------------------------------
# upload_do 为用户上传文件界面提供入口
@main.route('/upload_do/', methods=['GET', 'POST'])
@login_required
def upload():
    def unzip_file(zipfilename, unziptodir):
        # unzip_file 可将压缩文件解包

        # --------------------------------------------------------
        # 注：需修改 zipfile 源代码包含 flags & 0x800 的两个
        # if 代码段，将默认编码方式改为 gbk（windows下）。

        if not os.path.exists(unziptodir):
            os.mkdir(unziptodir, 0x0777)
        zfobj = zipfile.ZipFile(zipfilename)
        baseDir = zfobj.namelist()[0]
        for name in zfobj.namelist():
            for inffix in current_app.config['ZENITH_INVALID_INFFIX']:
                if inffix in name:
                    if inffix == '/':
                        count = name.count('//')
                        if count < 1:
                            continue
                    flash('您上传的压缩包中存在违例文件！')
                    abort(403)
            writeName = name
            if '/' in writeName:
                writeName = writeName.replace('/',
                        current_app.config['ZENITH_PATH_SEPERATOR'])
            if '\\' in writeName:
                writeName = writeName.replace('\\',
                        current_app.config['ZENITH_PATH_SEPERATOR'])
            if writeName.endswith(current_app.config['ZENITH_PATH_SEPERATOR']):
                # 此文件是目录
                os.mkdir(os.path.join(unziptodir, writeName))
            else:
                ext_filename = os.path.join(unziptodir, writeName)
                ext_dir= os.path.dirname(ext_filename)
                if not os.path.exists(ext_dir):
                    os.mkdir(ext_dir,0x0777)
                outfile = open(ext_filename, 'wb')
                outfile.write(zfobj.read(name))
                outfile.close()
        return baseDir

    def clear(dir):
        # clear 函数用于将产生的temp文件清空
        shutil.rmtree(dir)

    path = request.args.get('path', '/upload/', type=str)
        # 用户要将文件上传到的目录

    # 当路径不为根目录时，检查该路径对于当前用户是否合法（该用户是否已创建该目录）
    if path != '/':
        if len(path.split('/')) < 3 or path[-1] != '/':
            abort(403)
        ___filename = path.split('/')[-2]
        ___filenameLen = -(len(___filename)+1)
        ___path = path[:___filenameLen]
        isPath = File.query.filter("path=:p and isdir=1 "
                                   "and filename=:f and ownerid=:d").\
                            params(p=___path,
                                   f=___filename,
                                   d=current_user.uid).first()
        if isPath is None or isPath.owner != current_user:
            abort(403)

    form = UploadForm()
    if form.validate_on_submit():
        isPrivate = not form.share.data
        while True:
            randomBasePath = current_app.\
                config['ZENITH_TEMPFILE_STORE_PATH'] + \
                ''.join(random.sample(
                        current_app.\
                            config['ZENITH_RANDOM_PATH_ELEMENTS'],
                        current_app.\
                            config['ZENITH_TEMPFOLDER_LENGTH']))
            if os.path.exists(randomBasePath):
            # 若创建的随机目录已存在则重新创建
                continue
            os.mkdir(randomBasePath)
            randomBasePath += current_app.\
                config['ZENITH_PATH_SEPERATOR']
            break
        filename = form.file.data.filename
        for invalidInffix in current_app.config['ZENITH_INVALID_INFFIX']:
            # 保证文件名安全
            if invalidInffix in filename:
                flash('您上传的文件名不合法，请检查并重新上传！')
                return redirect(url_for('main.upload',
                                        path =path,
                                        _external=True))

        form.file.data.save(
                randomBasePath + filename)  # 使用用户文件名保存文件
        if not os.path.exists(
                randomBasePath + filename): # 验证文件存在
            abort(500)

        if filename.split('.')[-1] == \
            current_app.config['ZENITH_FOLDER_ZIP_SUFFIX']:
            toAdd = 0   # 记录要增加的用户云盘使用量
            left = current_user.maxm - current_user.used    # 剩余量
            # 用户上传的是一个目录
            baseDir = None  # 用户上传压缩包代表的目录名
            try:
                baseDir = unzip_file(
                        randomBasePath + filename,
                        randomBasePath)
                zipflag = True
            except:
                # 上传目录无法使用 zip 解压，提示错误
                flash('您压缩的目录内容无法使用 zip 算法解压，'
                      '请重新检查后上传！')
                zipflag = False

            if not zipflag:
                # 无法解压则重定向回上传界面
                clear(randomBasePath)
                return redirect(url_for('main.upload',
                                        path=path,
                                        _external=True))

            if baseDir[-1] != '/':
                # 用户上传的压缩包中不包含任何目录，为单个文件
                flash('您上传的压缩包中未包含任何目录结构，'
                      '请检查后重新上传！')
                clear(randomBasePath)
                return redirect(url_for('main.upload',
                                        path=path,
                                        _external=True))

            basename = baseDir[:-1]
            tempname = baseDir[:-1]  # 确定要上传的目录下没有同名文件
            i = 0
            while 1:
                isSameExist = File.query.\
                    filter("path=:p and filename=:f and ownerid=:d").\
                    params(p=path,
                           f = tempname,
                           d=current_user.uid).first()
                sameType = '文件'
                if isSameExist:
                    if isSameExist.isdir:
                        sameType = '文件夹'
                    if i == 0:
                        tempname = basename + '-副本'
                    else:
                        tempname = basename + '-副本' + str(i)
                else:
                    if tempname != basename:
                        flash("目标目录存在同名" + sameType +
                              basename + "，已将您要上传的"
                              "目录重命名为 " + tempname)
                    break
                i += 1

            basePath = path + tempname
                # 解压出的目录中的所有文件路径前缀均需替换为此
            replacePathLen = len(randomBasePath + baseDir)
                # 解压出的目录在服务器中的所有文件路径前缀需要替换的长度
            os.remove(randomBasePath + filename)
                # 删除用户上传的压缩包

            # 向数据库创建压缩包根目录
            baseFolder = File(
                path = path,
                filename = tempname,
                perlink = '',
                cfileid = -1,
                isdir=True,
                linkpass = '',
                ownerid = current_user.uid,
                private = isPrivate,
                description = form.body.data
            )
            db.session.add(baseFolder)

            for parent, dirnames, filenames in os.walk(randomBasePath):
                # 父目录名称、所有文件夹名称（不含路径）、所有文件名称
                for _dirname in dirnames:
                    if _dirname == basename:
                        continue
                    # 遍历每个文件夹，创建目录结构
                    _dirpath = parent[replacePathLen:].\
                        strip(current_app.\
                              config['ZENITH_PATH_SEPERATOR'])
                    _dirpath = _dirpath.replace(
                            current_app.\
                                config['ZENITH_PATH_SEPERATOR'],
                            '/')
                    if _dirpath != '':
                        _dirpath += '/'
                        # 非根目录文件需要增加一个 '/'
                    _dirpath = basePath + '/' + _dirpath

                    # 在数据库创建目录记录
                    df = File(
                        filename = _dirname,
                        path = _dirpath,
                        perlink = '',
                        cfileid = -1,
                        isdir = True,
                        linkpass = '',
                        ownerid = current_user.uid,
                        private = isPrivate,
                        description= ''
                    )
                    db.session.add(df)

                for _filename in filenames:
                    md5 = CFILE.md5FromFile(
                            os.path.join(parent,
                                         _filename))
                        # 计算每个文件的 md5
                    cf = CFILE.query.filter("md5=:_md5").\
                        params(_md5=md5).first()
                    if cf is None:
                        # 此文件需加入 CFILE
                        cf = CFILE(
                            size=os.path.getsize(
                                os.path.join(parent,_filename)
                            ),
                            ref=1,
                            md5=md5,
                        )
                        toAdd += cf.size
                        if toAdd > left:
                            # 用户云盘空间不足
                            flash('您的云盘空间不足，仅为您上传部分文件！')
                            break
                        db.session.add(cf)
                        db.session.commit()
                        cf = CFILE.query.filter("md5=:_md5").\
                            params(_md5=md5).first()
                        if cf is None:
                            # 加入数据库失败
                            clear(randomBasePath)
                            abort(500)

                        shutil.copy(
                            os.path.join(parent, _filename),
                            current_app.\
                                config['ZENITH_FILE_STORE_PATH'] +
                                str(cf.uid)
                        )   # 拷贝文件到存储目录

                        if not os.path.exists(
                            os.path.join(current_app.\
                                config['ZENITH_FILE_STORE_PATH'],
                            str(cf.uid))):
                            # 拷贝文件失败，需撤销文件记录
                            db.session.delete(cf)
                            clear(randomBasePath)
                            abort(500)
                    else:
                        cf.ref += 1
                        db.session.add(cf)

                    _filePath = parent[replacePathLen:].\
                        strip(current_app.\
                              config['ZENITH_PATH_SEPERATOR'])
                    _filePath = _filePath.replace(
                            current_app.\
                                config['ZENITH_PATH_SEPERATOR'],
                            '/')
                    if _filePath != '':
                        _filePath += '/'
                    _filePath = basePath + '/' + _filePath

                    # 创建文件 FILE 记录
                    uf = File(
                        filename = _filename,
                        path = _filePath,
                        perlink = '',
                        cfileid = cf.uid,
                        isdir=False,
                        linkpass='',
                        private=isPrivate,
                        ownerid=current_user.uid,
                        description=''
                    )
                    db.session.add(uf)
            # 增加用户云盘使用量
            current_user.used += toAdd
            db.session.add(current_user)
            db.session.commit()
            clear(randomBasePath)

            if form.share.data:
                baseFolder = File.query.\
                                filter('filename=:_lfn and path=:_path '
                                       'and ownerid=:_id').\
                                params(_lfn = tempname,
                                       _path = path,
                                       _id = current_user.uid).\
                                first()
                if baseFolder is None:
                    abort(500)
                return redirect(url_for('main.set_share',
                                        id = baseFolder.uid,
                                        _external=True))
                # 不共享时跳转到云盘界面，路径为要上传的目录所在的路径
            return redirect(url_for('main.cloud',
                                    path=path,
                                    _external=True))

        else:
            # 用户上传的是单个普通文件
            md5 = CFILE.md5FromFile(
                    randomBasePath + filename)  # 计算文件 md5
            cfile = CFILE.query.\
                    filter("md5=:_md5").\
                    params(_md5=md5).first()        # 查询是否已存在对应文件

            if cfile is None:
                # 不存在相同 md5 的文件则创建 CFILE 记录
                cf = CFILE(
                    md5 = md5,
                    size = os.path.\
                        getsize(
                        randomBasePath +
                        filename
                    ),
                    ref = 1
                )
                if cf.size > current_user.maxm - \
                    current_user.used:
                    flash('您的云盘空间不足，无法上传！')
                    clear(randomBasePath)
                    return redirect(url_for('main.upload',
                                            path = path))
                current_user.used += cf.size
                db.session.add(cf)
                db.session.commit()
                    # commit 以获得 cfileid
                cf = CFILE.query.\
                    filter('md5=:_md5').\
                    params(_md5=md5).first()
                if cf is None:
                    clear(randomBasePath)
                    abort(500)
                shutil.copy(
                    randomBasePath + filename,
                    current_app.config['ZENITH_FILE_STORE_PATH'] +
                        str(cf.uid)
                )
                if not os.path.exists(
                    current_app.config['ZENITH_FILE_STORE_PATH'] +
                        str(cf.uid)
                ):
                    db.session.delete(cf)
                    clear(randomBasePath)
                    abort(500)
            else:
                cf = cfile      # 已存在相同 md5 文件
                cf.ref += 1
                db.session.add(cf)

            f = File(path = path,
                     filename = filename,
                     perlink = '',
                     cfileid = cf.uid,
                     isdir = False,
                     linkpass = '',
                     private = isPrivate,
                     owner = current_user,
                     description = form.body.data
                     )
            db.session.add(f)
            db.session.commit()
            f = File.query.\
                filter('filename=:_lfn and path=:_path '
                       'and ownerid=:_id').\
                params(_lfn = filename,
                       _path = path,
                       _id = current_user.uid).\
                first()
            clear(randomBasePath)

            db.session.add(current_user)

            if form.share.data:
                return redirect(url_for('main.set_share',
                                        id=f.uid,
                                        _external=True))
            return redirect(url_for('main.file',
                                    id = f.uid,
                                    _external=True))

    return render_template('main/load/upload.html',
                           form=form,
                           path=path)

# ----------------------------------------------------------------------
# copy 函数为用户复制文件/目录界面提供了入口，用户可通过此函数复制自己云盘中的
# 文件/目录。用户可选择按文件名/创建时间的顺/逆序排序。当用户点击界面中的 确认
# 按钮时，服务器将跳转到 copy_check 入口验证合法性并执行数据库写入操作。
@main.route('/copy/')
@login_required
def copy():
    path = request.args.get('path', '/', type=str)
        # 用户准备将某个文件/目录拷贝到的路径
    id = request.args.get('id', 0, type=int)
        # 用户准备拷贝的文件/目录的 uid
    order = request.args.get('order', 'time', type=str)
        # 用户选择的排序方式，按创建时间/名称
    direction = request.args.get('direction', 'front', type=str)
        # 用户选择的排序类型，顺序/逆序
    page = request.args.get('page', 1, type=int)
        # 当前路径下的文件/目录数过多时需分页
    if path == '':
        path='/'
    if id <= 0:
        abort(403)
    file = File.query.get(id)
    if file is None or file.owner != current_user:
        # 要拷贝的文件/目录不存在，或所有权不属于当前用户时返回 403 错误
        abort(403)

    # 当要拷贝到的路径不为根目录时，检查该路径对于当前用户是否合法（该用户
    #     是否已创建该目录）
    if path != '/':
        if len(path.split('/')) < 3 or path[-1] != '/':
            abort(403)
        ___filename = path.split('/')[-2]
        ___filenameLen = -(len(___filename)+1)
        ___path = path[:___filenameLen]
        isPath = File.query.\
            filter("path=:p and filename=:f and ownerid=:d").\
            params(p=___path,
                   f=___filename,
                   d=current_user.uid).first()
        if isPath is None or isPath.owner != current_user:
            abort(403)

    # 抽取所有当前路径下的目录并按用户指定方式排序
    query = current_user.files.\
        filter("path=:p and uid<>:id and isdir=1 and ownerid=:d").\
        params(p=path,
               id=file.uid,
               d=current_user.uid)
    if order == 'name':
        if direction == 'reverse':
            query = query.order_by(File.isdir.desc()).\
                order_by(File.filename.desc())
        else:
            query = query.order_by(File.isdir.desc()).\
                order_by(File.filename.asc())
    else:
        if direction == 'reverse':
            query = query.order_by(File.isdir.desc()).\
                order_by(File.created.asc())
        else:
            query = query.order_by(File.isdir.desc()).\
                order_by(File.created.desc())

    # 生成文件-类型列表并分页，模板根据文件类型显示图标
    pagination = query.paginate(page,
                                per_page=current_app.\
                                    config['ZENITH_FILES_PER_PAGE'],
                                error_out=False)
    files = pagination.items
    file_types = generateFileTypes(files)
    return render_template('main/copy/copy.html',
                           _file=file,
                           _path=path,
                           files=file_types,
                           _order=order,
                           curpath=path,
                           _direction=direction,
                           pagination = pagination,
                           pathlists=generatePathList(path))

# -----------------------------------------------------------------------------
# copy_check 是验证用户复制操作的入口，当前用户根据传入的 token 验证合法性并向数据库
# 执行写入操作。若用户要复制的是目录，则 copy_check 会将待复制目录下所有关联文件一起
# 拷贝
@main.route('/copy_check/<token>', methods=['GET'])
@login_required
def copy_check(token):
    fileid_path = current_user.copy_token_verify(token)
        # 用户模型自定义方法，返回一个列表，列表包含两个元素：待拷贝文件/目录的 Id 和
        #     准备拷贝到的目标路径
    if fileid_path is None:
        abort(403)
    _path = fileid_path[1]
    _fileid = fileid_path[0]
    if _path is None or _fileid is None or _fileid <= 0:
        abort(403)
    file = File.query.get_or_404(_fileid)
    if file.owner != current_user:
        abort(403)

    # 当要拷贝到的路径不为根目录时，检查该路径对于当前用户是否合法（该用户
    #     是否已创建该目录）
    if _path != '/':
        if len(_path.split('/')) < 3 or _path[-1] != '/':
            abort(403)
        ___filename = _path.split('/')[-2]
        ___filenameLen = -(len(___filename)+1)
        ___path = _path[:___filenameLen]
        isPath = File.query.\
            filter("path=:p and isdir=1 and "
                   "filename=:f and ownerid=:d").\
            params(p=___path,
                   f=___filename,
                   d=current_user.uid).first()
        if isPath is None or isPath.owner != current_user:
            abort(403)

    # 考虑到目标路径可能已存在同名文件，此时需要将待复制目录/文件重命名，在其后附加
    #     '-副本'，若目标路径也已存在带有 '-副本' 后缀的文件，则在 '-副本' 后附加
    #     数字，如 '-副本0'，'-副本1'。tempname 用于存储重命名后的文件名。
    tempname = file.filename
    i = 0       # 确定是第几次增加后缀，即根据 i 添加 '-副本i'
    while 1:
        isSameExist = File.query.\
            filter("path=:p and filename=:f and ownerid=:d").\
            params(p=_path,
                   f = tempname,
                   d=current_user.uid).first()

        sameType = '文件'
        if isSameExist:
            # 寻找到同名文件
            if isSameExist.isdir:
                sameType = '文件夹'
            if file.isdir:  # 待拷贝为目录时，只需在目录名后添加 '-副本i'
                type = "文件夹"
                if i == 0:
                    tempname = file.filename + '-副本'
                else:
                    tempname = file.filename + '-副本' + str(i)
            else:           # 待拷贝为文件时，需在文件后缀名前添加 '-副本i'
                type = "文件"
                suffix = file.filename.split('.')[-1]
                if suffix == file.filename:     # 待拷贝文件无后缀名
                    if i == 0:
                        tempname = file.filename + '-副本'
                    else:
                        tempname = file.filename + '-副本' + str(i)
                else:
                    if i == 0:
                        tempname = file.\
                            filename[:len(file.filename)-len(suffix)-1] + \
                            '-副本.' + suffix
                    else:
                        tempname = file.\
                            filename[:len(file.filename)-len(suffix)-1] + \
                            '-副本' + str(i) + '.' + suffix
        else:
            if tempname != file.filename:
                # 若 tempname 与原文件/目录名不同说明存在同名文件
                flash("目标目录存在同名" + sameType + file.filename +
                      "，已将您要复制的" + type + "重命名为 " + tempname)
            break
        i += 1

    # 开始向数据库中复制记录
    if file.isdir:
        # 用户试图拷贝目录
        movePath = file.path + file.filename + '/'
        filelist = File.query.\
            filter("path like :p and ownerid=:id").\
            params(id=current_user.uid,
                   p=movePath+'%')
        baseLen = len(file.path + file.filename)
            # 记录待拷贝目录下的文件的路径中，需要被替换的长度。例如有文件为
            # [/home/forec][/work/a.jpg]，要拷贝目录 forec 到路径 /usr/
            # 下，假设存在同名文件夹，则将 forec 重命名为 forec-副本。则
            # a.jpg 的新路径为 /usr/forec-副本[/work/a.jpg]，即原路径的后
            # 半部分复用，而前半部分的长度为 baseLen。
        for _file in filelist:
            if not _file.isdir and _file.cfileid > 0:
                # 拷贝非空文件需要增加用户已使用的云盘空间
                current_user.used += _file.cfile.size
            newPath = _path + tempname + _file.path[baseLen:]
                # newPath 为文件要复制到的新路径，此路径由三部分构成：
                # 用户指定的拷贝路径 + 用户要复制的目录重命名后的名称 +
                # 复用的原始子路径
            newFile = File(ownerid=_file.ownerid,
                           cfileid=_file.cfileid,
                           path=newPath,
                           perlink='',
                           filename=_file.filename,
                           linkpass='',
                           isdir=_file.isdir,
                           description=_file.description)
            db.session.add(newFile)
            db.session.commit()
                # commit 后才可获得 uid，生成资源外链
            newFile.perlink = url_for('main.file',
                                      id=newFile.uid,
                                      _external=True)
            db.session.add(newFile)
            if current_user.used > current_user.maxm:
                # 用户云盘空间不足
                message = Message(sender=User.query.offset(1).first(),
                                  receiver=current_user,
                                  message='您的云盘空间已满，请及时清理！')
                db.session.add(message)
                flash('您的云盘空间已满！')
    else:
        # 用户试图拷贝文件
        if file.cfileid > 0:
            if current_user.used + file.cfile.size > current_user.maxm:
                flash('您的云盘空间不足，无法拷贝！')
                return redirect(url_for('main.file',
                                        id=file.uid,
                                        _external=True))

    # 无论如何都需要拷贝最开始的文件/目录
    newRootFile = File(ownerid=file.ownerid,
                    cfileid=file.cfileid,
                    path=_path,
                    perlink='',
                    filename=tempname,
                    linkpass='',
                    isdir=file.isdir,
                    description=file.description)
    db.session.add(newRootFile)
    db.session.commit()
    newRootFile.perlink = url_for('main.file',
                                  id=newRootFile.uid,
                                  _external=True)
    db.session.add(newRootFile)

    # 提示消息
    if file.isdir:
        flash('文件夹 ' + movePath + ' 已拷贝到 ' + _path + '下')
    else:
        current_user.used += file.cfile.size
        flash('文件 ' + file.path + file.filename +
              ' 已拷贝到 ' + _path + '下')
    db.session.add(current_user)
    # 复制成功重定向到新文件的详细界面或目录的云盘
    if not file.isdir:
        return redirect(url_for('main.file',
                                id=newRootFile.uid,
                                _external=True))
    else:
        return redirect(url_for('main.cloud',
                                path= newRootFile.path,
                                _external=True))

# ---------------------------------------------------------------------
# move 函数为用户移动文件/目录界面提供了入口，用户可通过此函数移动自己云盘中的
# 文件/目录。用户可选择按文件名/创建时间的顺/逆序排序。当用户点击界面中的 确认
# 按钮时，服务器将跳转到 move_check 入口验证合法性并执行数据库写入操作。
@main.route('/move/')
@login_required
def move():
    path = request.args.get('path', '/', type=str)
        # 用户准备将某个文件/目录移动到的路径
    id = request.args.get('id', 0, type=int)
        # 用户准备移动的文件/目录的 uid
    order = request.args.get('order', 'time', type=str)
        # 用户选择的排序方式，按创建时间/名称
    direction = request.args.get('direction', 'front', type=str)
        # 用户选择的排序类型，顺序/逆序
    page = request.args.get('page', 1, type=int)
        # 当前路径下的文件/目录数过多时需分页
    if path == '':
        path='/'
    if id <= 0:
        abort(403)
    file = File.query.get(id)
    if file is None or file.owner != current_user:
        abort(403)

    # 当要拷贝到的路径不为根目录时，检查该路径对于当前用户是否合法（该用户
    #     是否已创建该目录）
    if path != '/':
        if len(path.split('/')) < 3 or path[-1] != '/':
            abort(403)
        ___filename = path.split('/')[-2]
        ___filenameLen = -(len(___filename)+1)
        ___path = path[:___filenameLen]
        isPath = File.query.\
            filter("path=:p and filename=:f and ownerid=:d").\
            params(p=___path,
                   f=___filename,
                   d=current_user.uid).first()
        if isPath is None or isPath.owner != current_user:
            abort(403)

    # 抽取所有当前路径下的文件/目录并按用户指定方式排序
    query = current_user.files.\
        filter("path=:p and uid<>:id and isdir=1 and ownerid=:d").\
        params(p=path,
               id=file.uid,
               d=current_user.uid)
    if order == 'name':
        if direction == 'reverse':
            query = query.order_by(File.isdir.desc()).\
                order_by(File.filename.desc())
        else:
            query = query.order_by(File.isdir.desc()).\
                order_by(File.filename.asc())
    else:
        if direction == 'reverse':
            query = query.order_by(File.isdir.desc()).\
                order_by(File.created.asc())
        else:
            query = query.order_by(File.isdir.desc()).\
                order_by(File.created.desc())

    # 生成文件-类型列表并分页，模板根据文件类型显示图标
    pagination = query.paginate(page,
                                per_page=current_app.\
                                    config['ZENITH_FILES_PER_PAGE'],
                                error_out=False)
    files = pagination.items
    file_types = generateFileTypes(files)
    return render_template('main/move/move.html',
                           _file=file,
                           _path=path,
                           files=file_types,
                           _order=order,
                           curpath=path,
                           _direction=direction,
                           pagination = pagination,
                           pathlists=generatePathList(path))

# -----------------------------------------------------------------------------
# move_check 是验证用户移动操作的入口，当前用户根据传入的 token 验证合法性并向数据库
# 执行写入操作。若用户要移动的是目录，则 fork_check 会将待移动目录下所有关联文件一起
# 移动
@main.route('/move_check/<token>', methods=['GET'])
@login_required
def move_check(token):
    fileid_path = current_user.move_token_verify(token)
        # 用户模型自定义方法，返回一个列表，列表包含两个元素：待移动文件/目录的 Id 和
        #     准备移动到的目标路径
    if fileid_path is None:
        abort(403)
    _path = fileid_path[1]
    _fileid = fileid_path[0]
    if _path is None or _fileid is None or _fileid <= 0:
        abort(403)
    file = File.query.get_or_404(_fileid)
    if file.owner != current_user:
        abort(403)

    # 当要移动到的路径不为根目录时，检查该路径对于当前用户是否合法（该用户
    #     是否已创建该目录）
    if _path != '/':
        if len(_path.split('/')) < 3 or _path[-1] != '/':
            abort(403)
        ___filename = _path.split('/')[-2]
        ___filenameLen = -(len(___filename)+1)
        ___path = _path[:___filenameLen]
        isPath = File.query.\
            filter("path=:p and isdir=1 and filename=:f and ownerid=:d").\
            params(p=___path,
                   f=___filename,
                   d =current_user.uid).first()
        if isPath is None or isPath.owner != current_user:
            abort(403)

    # 移动后的名称，与 copy_check 中的 tempname 相同
    tempname = file.filename
    i = 0
    while 1:
        isSameExist = File.query.\
            filter("path=:p and filename=:f and ownerid=:d").\
            params(p=_path,
                   f = tempname,
                   d=current_user.uid).first()

        sameType = '文件'
        if isSameExist:
            if isSameExist.isdir:
                sameType = '文件夹'
            if isSameExist.uid == file.uid:
                # 若要移动到的目录为当前文件所在目录，则无需移动
                if file.isdir:
                    flash("您要移动的文件夹" + file.filename +
                          "已在目标目录，无需移动！")
                else:
                    flash("您要移动的文件" + file.filename +
                          "已在目标目录，无需移动！")
                return redirect(url_for('main.file',
                                        id=file.uid,
                                        _external=True))
            if file.isdir:
                type = "文件夹"
                if i == 0:
                    tempname = file.filename + '-副本'
                else:
                    tempname = file.filename + '-副本' + str(i)
            else:
                type = "文件"
                suffix = file.filename.split('.')[-1]
                    # 获取文件后缀名，若文件没有后缀名则 suffix 和文件名相同
                if suffix == file.filename:
                    if i == 0:
                        tempname = file.filename + '-副本'
                    else:
                        tempname = file.filename + '-副本' + str(i)
                else:
                    if i == 0:
                        tempname = file.\
                            filename[:len(file.filename)-len(suffix)-1] + \
                            '-副本.' + suffix
                    else:
                        tempname = file.\
                            filename[:len(file.filename)-len(suffix)-1] + \
                            '-副本' + str(i) + '.' + suffix
        else:
            if tempname != file.filename:
                flash("目标目录存在同名" + sameType + file.filename +
                      "，已将您要移动的" + type + "重命名为 " + tempname)
            break
        i += 1

    if file.isdir:
        # 用户试图移动目录
        movePath = file.path + file.filename + '/'
        filelist = File.query.\
            filter("path like :p and ownerid=:id").\
            params(id=current_user.uid,
                   p=movePath+'%')
        baseLen = len(file.path + file.filename)
        for _file in filelist:
            newPath = _path + tempname +  _file.path[baseLen:]
            _file.path = newPath
            db.session.add(_file)
        flash('文件夹 ' + movePath + ' 已移动到 ' + _path + '下')

    # 更新根部文件/目录
    file.path = _path
    file.filename = tempname
    db.session.add(file)
    if not file.isdir:
        flash('文件 ' + file.path + file.filename +
              ' 已移动到 ' + _path + '下')
    return redirect(url_for('main.file',
                            id=file.uid,
                            _external=True))

# ----------------------------------------------------------------
# fork 函数提供了一个简单的验证界面，用户需要输入要 fork 的文件/目录的
# 提取码。如果该文件/目录为私有且不属于当前用户，则返回 403 错误。用户
# 无法 fork 自己的文件/目录。用户验证提取码正确后，会跳转到 fork_do 入
# 口选择要 fork 的路径。
@main.route('/fork/<int:id>', methods=['GET', 'POST'])
@login_required
def fork(id):
    file = File.query.get_or_404(id)
    if file is not None and file.owner == current_user:
        flash('您无法 Fork 自己的文件或目录')
        if file.isdir:
            return redirect('main.cloud', path=file.path)
        else:
            return redirect('main.file', id=file.uid)
    if file is None or file.private == True:
        abort(403)
    if file.linkpass is None or \
        file.linkpass == '' or \
        current_user.can(Permission.ADMINISTER):
        return redirect(url_for('main.fork_do',
                                path = '/',
                                id = file.uid,
                                _pass = file.linkpass,
                                _external=True))
    form = ConfirmShareForm()
    if form.validate_on_submit():
        if form.password.data == file.linkpass:
            return redirect(url_for('main.fork_do',
                                    path = '/',
                                    id = file.uid,
                                    _pass = file.linkpass,
                                    _external=True))
        else:
            flash('提取码错误！')
            return redirect(url_for('main.fork',
                                    id=file.uid,
                                    _external=True))
    return render_template('main/fork/fork_verify.html',
                           file=file,
                           form=form)

# ---------------------------------------------------------------------
# fork_do 函数为用户 Fork 文件/目录界面提供了入口，用户可通过此函数 Fork 其他
# 用户共享的文件/目录。用户无法 fork 自己的资源，当用户试图 fork 其他用户资
# 源时，若该资源为私有，则用户将无权限 fork；若资源为共享，则用户需要输入该
# 文件/目录的提取码（提取码由资源所有者设置，如果提取码留空则任何已登陆用户可
# 以直接下载）。当用户点击界面中的 确认 按钮时，服务器将跳转到 fork_check
# 入口验证合法性并执行数据库写入操作。
# fork_do 入口需要提供如下参数：
#   * 当前正在查看的路径，点击确定则跳转到 fork_check 确认合法性并写入数据库
#   * 当前目录下子文件/目录过多时需分页，用户指定的页码
#   * 要 fork 的资源 uid
#   * 要 fork 的资源的提取码
#   * 用户选择的排序方式
#   * 用户选择的排序类型
@main.route('/fork_do/')
@login_required
def fork_do():
    path = request.args.get('path', '/', type=str)
        # 用户准备将某个文件/目录 Fork 到的路径
    _fileid = request.args.get('id', 0, type=int)
        # 用户准备 Fork 的文件/目录的 uid
    order = request.args.get('order', 'time', type=str)
        # 用户选择的排序方式，按创建时间/名称
    direction = request.args.get('direction', 'front', type=str)
        # 用户选择的排序类型，顺序/逆序
    page = request.args.get('page', 1, type=int)
        # 当前路径下的文件/目录数过多时需分页
    _pass = request.args.get('_pass', '', type=str)
        # 用户提供的要 Fork 的资源的提取码，可能不正确

    if path == '':
        path='/'
    if _fileid <= 0:
        abort(403)
    file = File.query.get_or_404(_fileid)
    if file is not None and file.owner == current_user:
        flash('您无法 Fork 自己的文件或目录')
        if file.isdir:
            return redirect('main.cloud', path=file.path)
        else:
            return redirect('main.file', id=file.uid)
    if file is None or \
        file.private == True or \
        file.linkpass != _pass:
        # 资源不存在或资源私有或提取码不正确
        abort(403)

    # 当要 Fork 到的路径不为根目录时，检查该路径对于当前用户是否合法（该用户
    #     是否已创建该目录）
    if path != '/':
        if len(path.split('/')) < 3 or path[-1] != '/':
            abort(403)
        ___filename = path.split('/')[-2]
        ___filenameLen = -(len(___filename)+1)
        ___path = path[:___filenameLen]
        isPath = File.query.filter("path=:p and filename=:f and ownerid=:d").\
            params(p=___path, f=___filename, d=current_user.uid).first()
        if isPath is None or isPath.owner != current_user:
            abort(403)

    # 抽取所有当前路径下的目录并按用户指定方式排序
    query = current_user.files.\
        filter("path=:p and ownerid=:d and isdir=1").\
        params(p=path,
               d=current_user.uid)
    if order == 'name':
        if direction == 'reverse':
            query = query.order_by(File.isdir.desc()).\
                order_by(File.filename.desc())
        else:
            query = query.order_by(File.isdir.desc()).\
                order_by(File.filename.asc())
    else:
        if direction == 'reverse':
            query = query.order_by(File.isdir.desc()).\
                order_by(File.created.asc())
        else:
            query = query.order_by(File.isdir.desc()).\
                order_by(File.created.desc())

    # 分页
    pagination = query.paginate(page,
                                per_page=current_app.\
                                    config['ZENITH_FILES_PER_PAGE'],
                                error_out=False)
    files = pagination.items
    file_types = generateFileTypes(files)
    return render_template('main/fork/fork.html',
                           _file=file,
                           _path=path,
                           files=file_types,
                           _order=order,
                           curpath=path,
                           _direction=direction,
                           pagination = pagination,
                           _pass=_pass,
                           pathlists=generatePathList(path))

# -----------------------------------------------------------------------------
# fork_check 是验证用户 Fork 操作的入口，当前用户根据传入的 token 验证合法性并向数据库
# 执行写入操作。若用户要 Fork 的是目录，则 fork_check 会将待移动目录下所有关联文件一起
# 移动
@main.route('/fork_check/<token>', methods=['GET'])
@login_required
def fork_check(token):
    fileid_path_pass = current_user.fork_token_verify(token)
        # 用户模型自定义方法，返回一个列表，列表包含三个元素：待 Fork 文件/目录的 Id、
        #     准备移动到的目标路径以及待 Fork 资源的提取码
    if fileid_path_pass is None:
        abort(403)
    _path = fileid_path_pass[1]
    _fileid = fileid_path_pass[0]
    _pass = fileid_path_pass[2]
    if _path is None or _fileid is None or _fileid <= 0:
        abort(403)
    file = File.query.get_or_404(_fileid)
    if file is None or \
        file.private == True or \
        file.linkpass!= _pass:
        # 资源不存在或资源为私有或资源提取码不正确
        abort(403)

    if file is not None and file.owner == current_user:
        # 检查是否当前用户已为资源所有者
        flash('您无法 Fork 自己的文件或目录')
        if file.isdir:
            return redirect('main.cloud', path=file.path)
        else:
            return redirect('main.file', id=file.uid)

    # 当要 Fork 到的路径不为根目录时，检查该路径对于当前用户是否合法（该用户
    #     是否已创建该目录）
    if _path != '/':
        if len(_path.split('/')) < 3 or _path[-1] != '/':
            abort(403)
        ___filename = _path.split('/')[-2]
        ___filenameLen = -(len(___filename)+1)
        ___path = _path[:___filenameLen]
        isPath = File.query.\
            filter("path=:p and isdir=1 and "
                   "filename=:f and ownerid=:d").\
            params(p=___path,
                   f=___filename,
                   d=current_user.uid).first()
        if isPath is None or isPath.owner != current_user:
            abort(403)

    # tempname 为可能的重命名后的资源名，与 copy 和 move 操作中相同
    # 以下 while 循环检查同名文件方式与 copy 和 move 的 check 操作
    # 完全相同
    tempname = file.filename
    i = 0
    while 1:
        isSameExist = File.query.\
            filter("path=:p and filename=:f and ownerid=:d").\
            params(p=_path,
                   f = tempname,
                   d = current_user.uid).first()

        sameType = '文件'
        if isSameExist:
            if isSameExist.isdir:
                sameType = '文件夹'
            if file.isdir:
                type = "文件夹"
                if i == 0:
                    tempname = file.filename + '-副本'
                else:
                    tempname = file.filename + '-副本' + str(i)
            else:
                type = "文件"
                suffix = file.filename.split('.')[-1]
                if suffix == file.filename:
                    if i == 0:
                        tempname = file.filename + '-副本'
                    else:
                        tempname = file.filename + '-副本' + str(i)
                else:
                    if i == 0:
                        tempname = file.\
                            filename[:len(file.filename)-len(suffix)-1] + \
                            '-副本.' + suffix
                    else:
                        tempname = file.\
                            filename[:len(file.filename)-len(suffix)-1] + \
                            '-副本' + str(i) + '.' + suffix
        else:
            if tempname != file.filename:
                flash("目标路径存在同名" + sameType + file.filename +
                      "，已将您要 Fork 的" + type + "重命名为 " + tempname)
            break
        i += 1

    if file.isdir:
        # 用户试图 Fork 整个目录
        movePath = file.path + file.filename + '/'
        filelist = File.query.\
            filter("path like :p and ownerid=:id and private=0").\
            params(id=file.ownerid,
                   p=movePath+'%')
            # 筛选该目录下所有的非私有文件

        baseLen = len(file.path + file.filename)
            # 与 copy 和 check 中相同
        for _file in filelist:
            # 增加文件共享次数
            _file.shared += 1
            db.session.add(_file)
            if not _file.isdir and _file.cfileid > 0:
                # 增加用户已使用的云盘容量大小
                current_user.used += _file.cfile.size
            newPath = _path + tempname +  _file.path[baseLen:]
            newFile = File(ownerid=current_user.uid,
                           cfileid=_file.cfileid,
                           path=newPath,
                           perlink='',
                           filename=_file.filename,
                           linkpass='',
                           isdir=_file.isdir,
                           description=_file.description
                           )
            db.session.add(newFile)
            db.session.commit()
                # commit 以获取 uid 来产生资源外链
            newFile.perlink = url_for('main.file',
                                      id=newFile.uid,
                                      _external=True)
            db.session.add(newFile)
            if current_user.used > current_user.maxm:
                # 用户已达到云盘可用空间上限
                message = Message(sender=User.query.offset(1).first(),
                                  receiver=current_user,
                                  message='您的云盘空间已满，请及时清理！')
                db.session.add(message)
                flash('您的云盘空间已满！')
    else:
        # 用户试图 Fork 一个文件
        if file.cfileid > 0:
            if current_user.used + file.cfile.size > current_user.maxm:
                # 资源不足时给出提示信息，并重定向到要 Fork 的资源
                flash('您的云盘空间不足，无法 Fork！')
                return redirect(url_for('main.file',
                                        id=file.uid,
                                        _external=True))

    # 增加源文件共享次数
    file.shared += 1
    db.session.add(file)

    # 添加根文件/目录的记录
    newRootFile = File(ownerid=current_user.uid,
                    cfileid=file.cfileid,
                    path=_path,
                    perlink='',
                    filename=tempname,
                    linkpass='',
                    isdir=file.isdir,
                    description=file.description)
    db.session.add(newRootFile)
    db.session.commit()
    newRootFile.perlink = url_for('main.file',
                                  id=newRootFile.uid,
                                  _external=True)
    db.session.add(newRootFile)
    if file.isdir:
        flash('已 Fork 用户 ' + file.owner.nickname + ' 的目录 ' +
              file.filename + ' 到 ' + _path + '下')
    else:
        current_user.used += file.cfile.size
        flash('已 Fork 用户 ' + file.owner.nickname + ' 的文件 ' +
              file.filename + ' 到 ' + _path + '下')
    db.session.add(current_user)
    return redirect(url_for('main.file',
                            id=newRootFile.uid,
                            _external=True))

# ------------------------------------------------------------------------
# newfolder 为用户创建目录提供了入口，用户可在云盘界面、复制、移动、Fork 的同
# 时创建新文件夹。此入口提供了简单的目录编辑界面，在确认创建后会重定向回原始URL。
@main.route('/newfolder/', methods=['GET', 'POST'])
@login_required
def newfolder():
    path = request.args.get('path', '/', type=str)
    if path is None:
        abort(403)

    # 当要创建文件夹的路径不为根目录时，检查该路径对于当前用户是否合法（该用户
    #     是否已创建该目录）
    if path != '/':
        if len(path.split('/')) < 3 or path[-1] != '/':
            abort(403)
        ___filename = path.split('/')[-2]
        ___filenameLen = -(len(___filename)+1)
        ___path = path[:___filenameLen]
        isPath = File.query.\
            filter("path=:_path and isdir=1 and "
                   "filename=:lfn and ownerid=:_id").\
            params(_path=___path,
                   lfn=___filename,
                   _id=current_user.uid).first()
        if isPath is None or isPath.owner != current_user:
            abort(403)

    form = NewFolderForm()
    if form.validate_on_submit():

        # 判断是否在同目录下存在同名文件/目录
        tempname = form.foldername.data
        i = 0
        while 1:
            isSameExist = File.query.\
                filter("path=:p and filename=:f and ownerid=:d").\
                params(p=path,
                       f = tempname,
                       d=current_user.uid).first()
            sameType = '文件'
            if isSameExist:
                if isSameExist.isdir:
                    sameType = '文件夹'
                if i == 0:
                    tempname = form.foldername.data + '-副本'
                else:
                    tempname = form.foldername.data + '-副本' + str(i)
            else:
                if tempname != form.foldername.data:
                    flash("目标目录存在同名" + sameType +
                          form.foldername.data + "，已将您要移动的"
                          "文件夹重命名为 " + tempname)
                break
            i += 1

        # 创建新目录
        f = File(filename=tempname,
                 isdir=True,
                 private=True,
                 path=path,
                 cfileid=-1,
                 linkpass='',
                 ownerid=current_user.uid,
                 description=form.body.data,
                 perlink=''
                 )
        db.session.add(f)
        db.session.commit()
        # 提交以获得 uid 并产生 perlink
        f = File.query.\
            filter('filename=:lfn and path=:_path and ownerid=:_id ').\
            params(lfn = tempname,
                   _path = path,
                   _id = current_user.uid).first()
        if f is None:
            abort(500)
        f.perlink = url_for('main.file',
                            id=f.uid,
                            _external=True)
        db.session.add(f)
        if form.share.data:
            return redirect(url_for('main.set_share',
                                    id=f.uid,
                                    _external=True))
        else:
            return redirect(url_for('main.file',
                                    id=f.uid,
                                    _external=True))
    return render_template('main/files/newfolder.html',
                           path = path,
                           form = form)

# ------------------------------------------------------------------------
# delete_message 为用户提供了删除聊天消息的入口，一条聊天消息的接收/发送方均
# 可删除消息，但删除操作仅限于从个人的视野中移除，对另一方并不产生影响。其效果
# 与 WeChat 的聊天记录删除相同。
@main.route('/delete-message/<int:id>')
@login_required
def delete_message(id):
    message = Message.query.get_or_404(id)
    if message.receiver == current_user:
        # 用户为消息的接收方，则将 recv_delete 标志位设为 1，表示
        # 接收方不再显示此消息
        message.recv_delete = True
        message.viewed = True
        message.sended = True
        if message.send_delete:
            db.session.delete(message)
        else:
            db.session.add(message)
        return redirect(url_for('main.chat',
                                id=message.sender.uid,
                                _external=True))
    elif message.sender == current_user:
        # 消息发送方删除消息，则将 send_delete 标志位设为 1
        message.send_delete = True
        if message.recv_delete:
            db.session.delete(message)
        else:
            db.session.add(message)
        return redirect(url_for('main.chat',
                                id=message.receiver.uid,
                                _external=True))
    else:
        abort(403)

# ----------------------------------------------------------------
# recall_message 为用户提供了发送消息撤回功能，功能与 QQ 的消息撤回
# 相同，超过 2 分钟的消息无法撤回。2 分钟以内，无论对方是否已读均可
# 撤回。撤回操作不可逆，消息将从数据库中移除。
@main.route('/recall-message/<int:id>')
@login_required
def recall_message(id):
    message = Message.query.get_or_404(id)
    if message.sender != current_user:
        abort(403)
    if datetime.utcnow() - message.created > timedelta(minutes=2):
        flash('消息发送超过两分钟，无法撤回')
    else:
        db.session.delete(message)
        flash('消息已被撤回')
    return redirect(url_for('main.chat',
                            id=message.receiver.uid,
                            _external=True))

# -----------------------------------------------------------------
# chat 提供了用户聊天入口。chat 的请求参数为聊天对方的用户 uid 标识，其
# 功能与 WeChat 类似，但因为浏览器从上向下显示网页，因此在模板中，发送窗口
# 设置在顶部，消息按创建时间排序，从近到远，从上向下排列。对于当前用户的未读
# 消息，模板会将其加粗并标以蓝底。一旦用户 B 访问过的与某用户 A 的 chat 入
# 口包含了一些用户 A 发送的未读消息，则包含的这些用户 A 发送的消息均会被置为
# 已读状态（因为消息过长时分页显示，因此只要用户没有访问过未读消息所在的页，该
# 消息均不会视为已读）。
@main.route('/chat/<int:id>', methods=['GET', 'POST'])
@login_required
def chat(id):
    page = request.args.get('page', 1, type=int)
    form = ChatForm()
    remote = User.query.get_or_404(id)
    if form.validate_on_submit():
        newMessage = Message(
            sender=current_user,
            receiver=remote,
            message=form.body.data,
        )
        db.session.add(newMessage)
        db.session.commit()
        flash("消息已发送")
        form.body.data= ''
        return redirect(url_for('main.chat',
                                id=id,
                                _external=True))

    _messages = Message.query.\
        filter("(sendid=:sid and targetid=:tid and recv_delete=0) or "
               "(sendid=:tid and targetid=:sid and send_delete=0)").\
        params(sid=remote.uid,
               tid=current_user.uid)
    pagination = _messages.order_by(Message.created.desc()).\
        paginate(page,
                 per_page=current_app.\
                    config['ZENITH_MESSAGES_PER_PAGE'],
                 error_out=False)

    # 更新聊天消息的已读状态
    _message = []
    for __message in pagination.items:
        # __message 为此页显示的消息
        if __message.viewed:
            _message.append((__message, True))
        else:
            _message.append((__message, False))
            __message.viewed = True
            __message.sended = True
            db.session.add(__message)

    return render_template('main/messages/chat.html',
                           sender=remote,
                           messages = _message,
                           form=form,
                           page=page,
                           pagination=pagination)

# ------------------------------------------------------------------------
# close_chat 为用户提供了一次性忽略某个用户所有未读消息的功能。
@main.route('/close-chat/<int:id>')
@login_required
def close_chat(id):
    remote = User.query.get_or_404(id)
    messageList = Message.query.\
        filter("sendid=:sid and targetid=:tid").\
        params(sid=remote.uid,
               tid=current_user.uid)
    for message in messageList:
        message.viewed = True
        message.sended = True
        db.session.add(message)
    return redirect(url_for('main.messages',
                            key='',
                            _external=True))

# ------------------------------------------------------------------------
# delete_chat 函数为用户提供了一次性删除某个用户所有聊天记录的功能，该函数
# 只会单方面影响消息对用户的可见性。当且仅当双方均删除某条消息时，该消息
# 才会从数据库中移除。
@main.route('/delete-chat/<int:id>')
@login_required
def delete_chat(id):
    remote = User.query.get_or_404(id)
    messageList = Message.query.\
        filter("(sendid=:sid and targetid=:tid) or "
               "(sendid=:tid and targetid=:sid)").\
        params(sid=remote.uid,
               tid=current_user.uid)
    for message in messageList:
        if current_user == message.receiver:
            message.recv_delete = True
            if message.send_delete:
                db.session.delete(message)
            else:
                db.session.add(message)
        else:
            message.send_delete = True
            if message.recv_delete:
                db.session.delete(message)
            else:
                db.session.add(message)
    flash("您与 " + remote.nickname + ' 的对话已删除！')
    return redirect(url_for('main.messages',
                            key='',
                            _external=True))

# ---------------------------------------------------------------
# set_share 为用户提供了设置文件共享属性的功能，提供了简单的设置密码
# 界面。此操作将递归进行，一旦某个目录被设置为共享，该目录下的所有文件/
# 目录，无论此前是否为私有，之后将均被设置为共享，并且提取码也将被更新。
@main.route('/set-share/<int:id>', methods=['GET','POST'])
@login_required
def set_share(id):
    file = File.query.get_or_404(id)
    if file is None or file.owner != current_user and \
            not current_user.can(Permission.ADMINISTER):
        # 检查资源权限是否属于当前用户
        abort(403)
    form = SetShareForm()
    if form.validate_on_submit():
        file.linkpass = form.password.data
        file.private = False
        db.session.add(file)
        if file.isdir:
            underFiles = File.query.\
                filter("path like :p and ownerid=:d and private=1").\
                params(p=file.path+file.filename+'/%',
                       d=file.ownerid).all()
            for _file in underFiles:
                _file.private = True
                _file.linkpass = file.linkpass
                db.session.add(_file)
            flash('已将目录 ' + file.path + file.filename +
                  ' 设为共享！共享密码为 ' + file.linkpass + '。')
            if file.owner != current_user and \
                    current_user.can(Permission.ADMINISTER):
                # 管理员设置时返回到主页，否则将出现 403 错误（访问一个
                #     不存在的网盘目录）
                return redirect(url_for('main.index',
                                        _external=True))
            else:
                return redirect(url_for('main.cloud',
                                        path=file.path,
                                        _external=True))
        else:
            flash('已将文件 ' + file.path + file.filename +
                  ' 设为共享！共享密码为 ' + file.linkpass + '。')
            return redirect(url_for('main.file',
                                    id=file.uid,
                                    _external=True))
    return render_template('main/share/set_share.html',
                           file=file,
                           form=form)

# -------------------------------------------------------------------
# set_private 是 set_share 的逆操作，将某个文件/目录及关联的目录/文件全部
# 设为私有。无论此前为私有或共享，此操作后所有关联文件均被更新为私有。
@main.route('/set-private/<int:id>')
@login_required
def set_private(id):
    file = File.query.get_or_404(id)
    if file is None or file.owner != current_user and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    file.private = True
    db.session.add(file)
    if file.isdir:
        # 对目录下的全部共享文件重置共享密码
        underFiles = File.query.\
            filter("path like :p and ownerid=:d and private=0").\
            params(p=file.path+file.filename+'/%',
                   d=file.ownerid).all()
        for _file in underFiles:
            _file.private = True
            db.session.add(_file)
        flash('目录 ' + file.path + file.filename + ' 已被设置为私有。')
        if file.owner != current_user and \
                current_user.can(Permission.ADMINISTER):
            return redirect(url_for('main.index',
                                    _external=True))
        else:
            return redirect(url_for('main.cloud',
                                    path=file.path,
                                    _external=True))
    else:
        flash('文件 ' + file.path + file.filename + ' 已被设置为私有。')
        return redirect(url_for('main.file',
                                id= file.uid,
                                _external=True))
